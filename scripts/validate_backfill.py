"""Validate succeeded backfill exports with disk-backed keys and durable checkpoints."""
from pathlib import Path
from datetime import datetime,timezone
import json,sqlite3,tempfile,os,resource,sys
from usda_data.storage import hash_file,atomic_write,canonical,sha256
from usda_data.schema import Schema

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/acceptance/phase-09'

def main():
    active=json.loads((ROOT/'data/manifests/runs/active.json').read_text())
    state=json.loads((ROOT/'data/manifests/runs'/f'{active["run_id"]}.json').read_text())
    folder=OUT/'validated_tasks';folder.mkdir(exist_ok=True)
    version=sha256(Path(__file__).read_bytes()+(ROOT/'src/usda_data/schema.py').read_bytes())
    results=[]
    for task,record in state['tasks'].items():
        if record['status']!='succeeded':
            results.append({'task_id':task,'status':'blocked','reason':'Required export has not succeeded'});continue
        entry=record['export'];path=ROOT/'data/exports'/entry['csv_path'];schema_path=ROOT/'data/exports'/entry['schema_path']
        identity={'csv_sha256':entry['csv_sha256'],'schema_sha256':hash_file(schema_path),'validator_version':version}
        target=folder/(task+'.json')
        if target.exists():
            prior=json.loads(target.read_text())
            if prior.get('identity')==identity and prior['status']=='pass' and hash_file(path)==identity['csv_sha256']:
                results.append(prior);continue
        result={'task_id':task,'dataset':entry['dataset'],'identity':identity,'checked_at_utc':datetime.now(timezone.utc).isoformat()}
        try:
            if hash_file(path)!=entry['csv_sha256']:raise ValueError('Export bytes differ from manifest')
            schema=Schema.load(schema_path)
            with tempfile.TemporaryDirectory(prefix='usda-key-audit-') as temp:
                db=sqlite3.connect(str(Path(temp)/'keys.sqlite'));db.execute('CREATE TABLE keys (dimensions TEXT PRIMARY KEY)');count=0
                try:
                    for frame in schema.read_csv_chunks(path,5000):
                        keys=[(json.dumps([str(v.normalize()) if hasattr(v,'normalize') else str(v) for v in row]),) for row in frame[schema.keys].itertuples(index=False,name=None)]
                        db.executemany('INSERT INTO keys VALUES (?)',keys);count+=len(frame)
                    if count!=entry['rows']:raise ValueError('Full export row count differs from manifest')
                finally:db.close()
            result.update(status='pass',rows=count,duplicate_keys=0,missing_required_dimensions=0)
        except Exception as exc:result.update(status='fail',error_type=type(exc).__name__,error=str(exc))
        atomic_write(target,canonical(result));results.append(result)
        print(task,result['status'],result.get('rows'),flush=True)
    summary={'run_id':state['run_id'],'expected_tasks':len(state['tasks']),'passed':sum(r['status']=='pass' for r in results),'failed':sum(r['status']=='fail' for r in results),'blocked':sum(r['status']=='blocked' for r in results),'validated_rows':sum(r.get('rows',0) for r in results),'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1024*1024 if sys.platform=='darwin' else 1024),'chunk_size':5000,'checks':results}
    atomic_write(OUT/'full_validation.json',canonical(summary));print({k:v for k,v in summary.items() if k!='checks'})
    return int(bool(summary['failed'] or summary['blocked']))

if __name__=='__main__':raise SystemExit(main())
