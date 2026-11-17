"""Command line interface sharing the public partition iterator."""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import tempfile
from . import __version__
from .api import iter_wasde, iter_costs_returns, iter_export_sales, iter_psd, iter_rma_sob
from .config import DATASETS
from .errors import ConfigurationError, USDAError
from .sources.wasde import SCHEMA, bounds
from .storage import atomic_write, canonical, hash_file


def export_frames(frames, output_dir, *, dataset="wasde", schema=SCHEMA):
    """Publish a complete immutable CSV and select it only after all reports pass."""
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
    fd,pending=tempfile.mkstemp(prefix='.pending-',dir=output)
    count=0;partitions=set();hash_value=hashlib.sha256()
    try:
        with os.fdopen(fd,'wb') as stream:
            header=schema.csv_bytes(schema.frame([]))
            stream.write(header);hash_value.update(header)
            for frame in frames:
                body=schema.csv_bytes(frame).split(b'\n',1)[1]
                stream.write(body);hash_value.update(body);count+=len(frame)
                if len(frame):
                    partitions.update(frame['snapshot_id'])
                # PDF/HTML parsers can retain cyclic page trees after yielding.
                # Reclaim them at each partition boundary, before loading another.
                del body
                gc.collect()
            stream.flush();os.fsync(stream.fileno())
        digest=hash_value.hexdigest()
        destination=output/dataset/digest/'data.csv';destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists():
            if hash_file(destination)!=digest:
                raise USDAError('Existing export is corrupt')
        else:
            os.replace(pending,destination)
        atomic_write(destination.parent/'schema.json',canonical(schema.to_dict()))
        manifest={'dataset':dataset,'csv_path':str(destination.relative_to(output)),'csv_sha256':digest,'rows':count,'snapshot_ids':sorted(partitions),'schema_path':str((destination.parent/'schema.json').relative_to(output))}
        atomic_write(output/f'{dataset}.latest.json',canonical(manifest))
        return manifest
    finally:
        Path(pending).unlink(missing_ok=True)


def export_wasde(frames, output_dir):
    return export_frames(frames,output_dir)

def main(argv=None):
    parser=argparse.ArgumentParser(prog='usda-data',description='Versioned USDA downloads and SQL-ready exports')
    parser.add_argument('--version',action='version',version=__version__)
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('list-datasets',help='List all seven frozen dataset IDs')
    sync=commands.add_parser('sync',help='Refresh every configured partition; resume failed jobs and publish only complete runs')
    sync.add_argument('--dataset',default='all',choices=(*DATASETS,'all'))
    sync.add_argument('--config',required=True)
    sync.add_argument('--data-dir');sync.add_argument('--output-dir');sync.add_argument('--resume',action='store_true')
    sync.add_argument('--dry-run',action='store_true',help='List configured jobs only; no numeric downloads. Discovery planning may read metadata.')
    validate=commands.add_parser('validate',help='Verify selected CSV schemas, keys, row counts and content hashes')
    validate.add_argument('--input-dir',required=True)
    calendar=commands.add_parser('calendar',help='Show saved official publication events with precision and stale-calendar labels')
    calendar.add_argument('--dataset',required=True,choices=(*DATASETS,'all'));calendar.add_argument('--config',default='config/calendar.json')
    calendar.add_argument('--timezone',default='Asia/Shanghai')
    fetch=commands.add_parser('fetch',help='Fetch a supported dataset and atomically publish a complete CSV')
    fetch.add_argument('--dataset',required=True,choices=(*DATASETS,'psd','all'))
    fetch.add_argument('--start',help='Inclusive WASDE publication date YYYY-MM-DD')
    fetch.add_argument('--end',help='Inclusive WASDE publication date YYYY-MM-DD')
    fetch.add_argument('--config',help='Explicit all-dataset task/range configuration')
    fetch.add_argument('--resume',action='store_true',help='Resume failed all-dataset configured tasks')
    fetch.add_argument('--dry-run',action='store_true',help='List configured jobs only; no numeric files. A separate discovery planner may read metadata.')
    fetch.add_argument('--commodity-years',help='RMA source commodity years: YYYY,YYYY or YYYY:YYYY')
    fetch.add_argument('--all-history',action='store_true',help='RMA: all discovered supported 1989-forward years; report 1948-1988 as unsupported')
    fetch.add_argument('--chunk-size',type=int,default=5000,help='RMA bounded row chunk size')
    fetch.add_argument('--report-start',help='Inclusive FAS report publication-date start, independent of marketing years')
    fetch.add_argument('--report-end',help='Inclusive FAS report publication-date end')
    fetch.add_argument('--with-reports',action='store_true',help='Archive the requested FAS report attachments alongside structured tables (also retained as parsing evidence)')
    fetch.add_argument('--market-years',help='ESR/PSD source marketing-year IDs: YYYY,YYYY or YYYY:YYYY')
    fetch.add_argument('--countries',default='all',help='ESR destination codes/names, comma-separated; default all')
    fetch.add_argument('--years',help='ERS observation years: YYYY,YYYY or inclusive YYYY:YYYY')
    fetch.add_argument('--commodities',default='all',help='ERS commodity/enterprise names, comma-separated; default all')
    fetch.add_argument('--data-dir')
    fetch.add_argument('--output-dir')
    fetch.add_argument('--force',action='store_true',help='Recheck source bytes; keep previous artifacts and versions')
    args=parser.parse_args(argv)
    try:
        if args.command=='list-datasets':
            print('\n'.join(DATASETS));return 0
        if args.command=='validate':
            from .sync import validate_export_root
            print(json.dumps(validate_export_root(args.input_dir),indent=2));return 0
        if args.command=='calendar':
            from .calendar import PublicationEvent,presentation,calendar_status
            from datetime import datetime,timezone
            source=json.loads(Path(args.config).read_text());events=[]
            for raw in source['events']:
                event=PublicationEvent(**raw)
                if args.dataset=='all' or event.dataset==args.dataset:events.append({**presentation(event,args.timezone),'calendar_status':calendar_status(event,datetime.now(timezone.utc))})
            print(json.dumps({'events':events,'freshness':'unknown unless an artifact check confirms availability','verified_claims':source.get('claims',[])},indent=2));return 0
        if args.command=='sync' or args.dataset=='all':
            from .sync import load_tasks,execute
            from dataclasses import asdict
            if args.command == 'fetch' and (any(getattr(args, name) for name in ('start','end','years','market_years','commodity_years','report_start','report_end','with_reports','all_history')) or args.commodities != 'all' or args.countries != 'all' or args.chunk_size != 5000):
                raise ConfigurationError('All-dataset ranges and filters must be specified per task in --config')
            if not args.config:raise ConfigurationError('All-dataset fetch/sync requires --config with source-specific ranges')
            config,tasks=load_tasks(args.config,dataset=args.dataset)
            data_dir=args.data_dir or config.get('data_dir','data');output_dir=args.output_dir or config.get('output_dir',str(Path(data_dir)/'exports'))
            if args.dry_run:
                print(json.dumps({'tasks':[asdict(t) for t in tasks],'numeric_downloads':False,'task_count':len(tasks)},indent=2));return 0
            result=execute(tasks,data_dir=data_dir,output_dir=output_dir,resume=args.resume,refresh=args.command=='sync' or getattr(args,'force',False))
            print(json.dumps(result,indent=2));return result['exit_code']
        if args.config or args.resume or args.dry_run:raise ConfigurationError('Configured dry-run/resume currently requires --dataset all or sync')
        args.data_dir=args.data_dir or 'data';args.output_dir=args.output_dir or str(Path(args.data_dir)/'exports')
        if args.dataset=='rma-sob':
            from .sources.rma_sob import SCHEMA as RMA_SCHEMA
            if not (args.commodity_years or args.all_history) or args.years or args.market_years or args.start or args.end or args.commodities!='all' or args.countries!='all' or args.report_start or args.report_end or args.with_reports:
                raise ConfigurationError('RMA requires --commodity-years or --all-history; other dataset range/filter options are unsupported')
            if args.chunk_size < 1:raise ConfigurationError('RMA chunk size must be positive')
            if args.all_history:print('Unsupported earlier layout: 1948-1988. Downloading discovered coverage-level years from 1989 onward.')
            manifest=export_frames(iter_rma_sob(args.commodity_years or [],data_dir=args.data_dir,refresh=args.force,chunk_size=args.chunk_size,all_history=args.all_history),args.output_dir,dataset='rma-sob',schema=RMA_SCHEMA)
            print(json.dumps(manifest,indent=2));return 0
        if args.commodity_years or args.all_history or args.chunk_size!=5000:
            raise ConfigurationError('RMA year/history/chunk options require rma-sob')
        if args.dataset in {'world-production','grain-trade','oilseed-trade'}:
            from .sources.report_datasets import iter_dataset,SCHEMA as REPORT_DATASET_SCHEMA
            if not args.market_years or not args.report_start or not args.report_end or args.start or args.end or args.years:
                raise ConfigurationError('Report datasets require --market-years and separate --report-start/--report-end')
            manifest=export_frames(iter_dataset(args.dataset,market_years=args.market_years,report_start=args.report_start,report_end=args.report_end,commodities=args.commodities,countries=args.countries,data_dir=args.data_dir,refresh=args.force),args.output_dir,dataset=args.dataset,schema=REPORT_DATASET_SCHEMA)
            print(json.dumps(manifest,indent=2));return 0
        if args.report_start or args.report_end or args.with_reports:
            raise ConfigurationError('Report options require one of the three FAS report datasets')
        if args.dataset=='psd':
            from .sources.fas_psd import SCHEMA as PSD_SCHEMA
            from .sources.fas_common import marketing_years
            if not args.market_years or args.start or args.end or args.years:
                raise ConfigurationError('PSD requires --market-years; other date/year options are unsupported')
            manifest=export_frames(iter_psd(args.commodities,marketing_years(args.market_years),countries=args.countries,data_dir=args.data_dir,refresh=args.force),args.output_dir,dataset='psd',schema=PSD_SCHEMA)
            print(json.dumps(manifest,indent=2));return 0
        if args.dataset=='export-sales':
            from .sources.fas_esr import SCHEMA as ESR_SCHEMA
            from .sources.fas_common import marketing_years
            if not args.market_years or args.start or args.end or args.years:
                raise ConfigurationError('ESR requires --market-years and does not accept other date/year options')
            years=marketing_years(args.market_years)
            manifest=export_frames(iter_export_sales(args.commodities,years,countries=args.countries,data_dir=args.data_dir,refresh=args.force),args.output_dir,dataset='export-sales',schema=ESR_SCHEMA)
            print(json.dumps(manifest,indent=2));return 0
        if args.market_years or args.countries!='all':
            raise ConfigurationError('Only ESR/PSD supports marketing-year/destination options in this phase')
        if args.dataset=='costs-returns':
            from .sources.ers_costs_returns import SCHEMA as ERS_SCHEMA, validate_years
            if not args.years or args.start or args.end:
                raise ConfigurationError('ERS requires --years; report-date bounds are unsupported')
            years=validate_years(args.years)
            manifest=export_frames(iter_costs_returns(years,commodities=args.commodities,data_dir=args.data_dir,refresh=args.force),args.output_dir,dataset='costs-returns',schema=ERS_SCHEMA)
            print(json.dumps(manifest,indent=2));return 0
        if args.dataset!='wasde':
            raise ConfigurationError('Requested adapter has not reached its implementation phase')
        if args.years or args.commodities!='all':
            raise ConfigurationError('WASDE does not accept ERS years/commodity filters')
        if not args.start or not args.end:
            raise ConfigurationError('WASDE requires --start and --end publication dates')
        bounds(args.start,args.end)
        manifest=export_wasde(iter_wasde(args.start,args.end,data_dir=args.data_dir,refresh=args.force),args.output_dir)
        print(json.dumps(manifest,indent=2));return 0
    except ConfigurationError as exc:
        parser.error(str(exc))
    except (USDAError,OSError,ValueError):
        # Only controlled exception types; no upstream bodies, headers or credentials.
        import sys
        print('Download or validation failed; inspect preserved source/partition evidence.',file=sys.stderr)
        return 1
