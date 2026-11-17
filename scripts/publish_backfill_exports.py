"""Publish seven aggregate CSVs only after all frozen tasks and report checks pass."""
from collections import defaultdict
from pathlib import Path
import hashlib,json,os,tempfile
from datetime import datetime,timezone
from usda_data.storage import atomic_write,canonical,hash_file
from usda_data.config import DATASETS

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/acceptance/phase-09'

def main():
    validation=json.loads((OUT/'full_validation.json').read_text());reports=json.loads((OUT/'report_backfill_summary.json').read_text())
    if validation['failed'] or validation['blocked'] or reports['failed'] or not reports.get('memory_within_budget'):raise RuntimeError('Full validation/report gate remains incomplete')
    base=ROOT/'data/exports';complete=json.loads((base/'complete.latest.json').read_text())
    if complete['status']!='complete' or complete['run_id']!=validation['run_id']:raise RuntimeError('No matching complete validated run')
    groups=defaultdict(list)
    for task,entry in complete['exports'].items():groups[entry['dataset']].append((task,entry))
    if set(groups)!=set(DATASETS):raise RuntimeError('All seven datasets are required')
    migrations={m['dataset']:m for m in json.loads((ROOT/'config/schema_migrations.json').read_text())['migrations']}
    output=base/'datasets';output.mkdir(exist_ok=True);manifests={}
    for dataset,entries in sorted(groups.items()):
        count=0;partitions=[];header=None;schema_body=None;digest=hashlib.sha256()
        fd,pending=tempfile.mkstemp(prefix='.pending-',dir=output)
        try:
            with os.fdopen(fd,'wb') as dest:
                for task,entry in sorted(entries):
                    source=base/entry['csv_path'];current_schema=(base/entry['schema_path']).read_bytes()
                    if hash_file(source)!=entry['csv_sha256']:raise RuntimeError('Changed input partition')
                    migration=migrations.get(dataset)
                    if migration:
                        if hashlib.sha256(current_schema).hexdigest() not in migration['source_schema_sha256']:raise RuntimeError('Schema migration does not authorize this exact source schema')
                        target_schema=(ROOT/migration['target_schema_path']).read_bytes()
                        if hashlib.sha256(target_schema).hexdigest()!=migration['target_schema_sha256']:raise RuntimeError('Pinned migration target changed')
                        source_definition=json.loads(current_schema);target_definition=json.loads(target_schema)
                        source_definition['version']=target_definition['version']
                        for field in source_definition['fields']:
                            if field['name']=='raw_record':field['meaning']=next(f['meaning'] for f in target_definition['fields'] if f['name']=='raw_record')
                        if source_definition!=target_definition:raise RuntimeError('Migration would conceal a structural or semantic field change')
                        current_schema=target_schema
                    if schema_body is not None and current_schema!=schema_body:raise RuntimeError('Mixed schemas cannot be concatenated')
                    schema_body=current_schema
                    with source.open('rb') as stream:
                        current_header=stream.readline()
                        if header is None:header=current_header;dest.write(header);digest.update(header)
                        if header!=current_header:raise RuntimeError('Partition CSV columns differ')
                        while chunk:=stream.read(1024*1024):dest.write(chunk);digest.update(chunk)
                    count+=entry['rows'];partitions.append({'task_id':task,**entry})
                dest.flush();os.fsync(dest.fileno())
            value=digest.hexdigest();folder=output/dataset/value;folder.mkdir(parents=True,exist_ok=True)
            target=folder/'data.csv'
            if target.exists():
                if hash_file(target)!=value:raise RuntimeError('Existing aggregate artifact corrupted')
            else:os.replace(pending,target)
            atomic_write(folder/'schema.json',schema_body)
            manifest={'dataset':dataset,'rows':count,'csv_sha256':value,'csv_path':str(target.relative_to(output)),'schema_path':str((folder/'schema.json').relative_to(output)),'snapshot_ids':sorted({s for _,e in entries for s in e['snapshot_ids']}),'partitions':partitions,'source_run_id':complete['run_id'],'status':'complete','schema_migration_id':migrations[dataset]['id'] if dataset in migrations else None}
            atomic_write(folder/'manifest.json',canonical(manifest));manifests[dataset]=manifest
            print(dataset,count,value,flush=True)
        finally:Path(pending).unlink(missing_ok=True)
    selection={'status':'complete','run_id':complete['run_id'],'configuration_hash':complete['configuration_hash'],'exports':manifests,'completed_at_utc':datetime.now(timezone.utc).isoformat()}
    atomic_write(output/'complete.latest.json',canonical(selection))
    for dataset,manifest in manifests.items():atomic_write(output/(dataset+'.latest.json'),canonical(manifest))
    atomic_write(OUT/'final_dataset_manifest.json',canonical(selection))

if __name__=='__main__':main()
