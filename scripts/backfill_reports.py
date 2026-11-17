"""Checkpoint every frozen report candidate with bounded worker memory and strict coverage."""
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,resource,sys,os
from usda_data.sources.reports import resolve_attachment,FAMILIES,DIRECTORY
from usda_data.sources.report_tables import parse_report,SCHEMA
from usda_data.storage import Store,atomic_write,canonical,hash_file,sha256
from usda_data.http import HTTPClient
from usda_data.config import HTTPConfig
from usda_data.errors import USDAError,DownloadError

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/acceptance/phase-09'

def rss():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1024*1024 if sys.platform=='darwin' else 1024)

def job(arguments):
    candidate,version,offline=arguments
    actual=sha256(b''.join((ROOT/'src/usda_data/sources'/name).read_bytes() for name in ['report_tables.py','report_dimension_repairs.json','report_source_gaps.json','reports.py']))
    if actual!=version:raise RuntimeError('Parser source changed during run; stop and resume with a fixed version')
    store=Store(ROOT/'data');family=candidate['report_family'];period=candidate['report_period']
    target=OUT/'report_partitions'/f'{family}-{period}.json'
    record={'family':family,'report_period':period,'url':candidate['url'],'parser_source_hash':version,'checked_at_utc':datetime.now(timezone.utc).isoformat()}
    class Offline:
        def get(self,*a,**kw):raise DownloadError('Uncached source artifact; live acquisition required')
    client=Offline() if offline else HTTPClient(HTTPConfig(trust_environment=False,max_attempts=2))
    try:
        body,receipt,resolved=resolve_attachment(client,store,candidate)
        record.update(source_artifact_id=receipt['source_artifact_id'],retrieved_at_utc=receipt['retrieved_at_utc'],bytes=len(body),source_status='available',resolved_url=resolved['url'])
        folder=store.root/'reports'/family/period/receipt['source_artifact_id']
        if not (folder/'report.pdf').exists():atomic_write(folder/'report.pdf',body)
        attachment={**resolved,**receipt,'report_family':family,'report_period':period,'attachment_path':str((folder/'report.pdf').relative_to(store.root))}
        atomic_write(folder/'manifest.json',canonical(attachment));record['attachment_path']=attachment['attachment_path']
        frame,evidence=parse_report(body,family,receipt,expected_period=period)
        snapshot=store.publish(family+'-reports-backfill',period,frame,SCHEMA,[receipt['source_artifact_id']],parser_version='report-source-'+version,configuration={'frozen_cutoff':'2026-11','family':family})
        coverage=store.root/'manifests/reports/backfill_coverage'/f'{family}-{period}-{version}.json'
        atomic_write(coverage,canonical(evidence))
        record.update(status='source_unavailable' if evidence.get('source_unavailable') else 'succeeded',source_unavailable_evidence=evidence.get('source_unavailable'),rows=len(frame),input_cells=evidence['input_cells'],table_instances=len(evidence['tables']),snapshot_id=snapshot['snapshot_id'],csv_path=snapshot['csv_path'],csv_sha256=snapshot['csv_sha256'],coverage_path=str(coverage.relative_to(store.root)))
    except USDAError as exc:record.update(status='failed',error_type=type(exc).__name__,error=str(exc))
    except Exception as exc:record.update(status='failed',error_type=type(exc).__name__,error='Unexpected parser/storage exception; inspect the source layout before retrying')
    finally:
        if not offline:client.close()
    record['worker_peak_rss_mib']=rss()
    atomic_write(target,canonical(record))
    return record

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers',type=int,default=1)
    parser.add_argument('--offline',action='store_true')
    parser.add_argument('--only-failed',action='store_true',help='Diagnostic subset; stale or unprocessed records still fail the full gate')
    args=parser.parse_args()
    if not 1<=args.workers<=2:parser.error('workers must be 1 or 2')
    store=Store(ROOT/'data');cutoff=json.loads((OUT/'resource_estimate.json').read_text())['client_cutoff_date'][:7]
    receipt=json.loads((store.root/'manifests/reports/urls'/f'{sha256(DIRECTORY.encode())}.json').read_text())
    directory=json.loads(store.artifact(receipt['source_artifact_id']).read_text());candidates=[]
    for year in directory['CircularSets']:
        for month in year['Months']:
            period=f'{int(year["CalendarYear"]):04}-{int(month["Item1"]):02}'
            if '2010-01'<=period<=cutoff:
                for family,(code,_,_) in FAMILIES.items():candidates.append({'report_family':family,'report_period':period,'url':f'https://apps.fas.usda.gov/PSDOnline/Circulars/{period[:4]}/{period[-2:]}/{code}.pdf','discovery_artifact_id':receipt['source_artifact_id']})
    frozen=OUT/'frozen_report_candidates.json'
    if frozen.exists():
        saved=json.loads(frozen.read_text())
        if saved['candidates']!=candidates:raise RuntimeError('Report inventory changed after freezing; reconcile explicitly before execution')
    else:atomic_write(frozen,canonical({'cutoff':cutoff,'directory_artifact_id':receipt['source_artifact_id'],'candidates':candidates}))
    version=sha256(b''.join((ROOT/'src/usda_data/sources'/name).read_bytes() for name in ['report_tables.py','report_dimension_repairs.json','report_source_gaps.json','reports.py']))
    jobs=[]
    for candidate in candidates:
        target=OUT/'report_partitions'/f'{candidate["report_family"]}-{candidate["report_period"]}.json'
        if target.exists():
            old=json.loads(target.read_text())
            if args.only_failed and old['status'] in {'succeeded','source_unavailable'}:continue
            if old.get('parser_source_hash')==version and old['status'] in {'succeeded','source_unavailable'} and hash_file(store.root/old['csv_path'])==old.get('csv_sha256'):continue
        jobs.append((candidate,version,args.offline))
    print(json.dumps({'frozen_candidates':len(candidates),'scheduled':len(jobs),'workers':args.workers,'parser_source_hash':version}),flush=True)
    worker_peaks=[]
    # A fresh process per PDF releases parser/native allocator memory deterministically.
    with ProcessPoolExecutor(max_workers=args.workers,max_tasks_per_child=1) as pool:
        for i,future in enumerate(as_completed([pool.submit(job,task) for task in jobs]),1):
            result=future.result();worker_peaks.append(result['worker_peak_rss_mib'])
            print(json.dumps({'completed':i,'family':result['family'],'period':result['report_period'],'status':result['status'],'error':result.get('error'),'worker_peak_rss_mib':result['worker_peak_rss_mib']}),flush=True)
    records=[json.loads((OUT/'report_partitions'/f'{c["report_family"]}-{c["report_period"]}.json').read_text()) for c in candidates]
    success=sum(r['status'] in {'succeeded','source_unavailable'} and r.get('parser_source_hash')==version for r in records)
    bound=rss()+sum(sorted(worker_peaks,reverse=True)[:args.workers])
    summary={'expected':len(candidates),'succeeded':success,'failed':len(candidates)-success,'parser_source_hash':version,'workers':args.workers,'peak_rss_mib':bound,'memory_measurement':'Conservative sum of parent peak and largest concurrent fresh-worker peaks','memory_budget_mib':512,'memory_within_budget':bound<=512,'processed_this_run':len(jobs)}
    atomic_write(OUT/'report_backfill_summary.json',canonical(summary));print(json.dumps(summary),flush=True)
    return int(success!=len(candidates) or bound>512)

if __name__=='__main__':raise SystemExit(main())
