"""Acquire only the reviewed ERS retry inventory with the package HTTP client."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime,timezone
from usda_data.http import HTTPClient
from usda_data.storage import sha256
ROOT=Path(__file__).resolve().parents[3]
jobs=json.loads((ROOT/'artifacts/acceptance/phase-03/retry_jobs.json').read_text())
def fetch(job):
 p=ROOT/job['path'];a=Path(str(p)+'.acquisition.json')
 prior=json.loads(a.read_text())
 if prior['status']==200:return {'id':job['id'],'status':'already_acquired'}
 with HTTPClient() as client:
  kind=p.suffix[1:];body,metadata=client.get(job['url'],expected=kind)
 if p.exists():p.rename(Path(str(p)+'.second-failure'))
 a.rename(Path(str(a)+'.second-failure'))
 p.write_bytes(body)
 record={**job,**metadata,'checked_at_utc':datetime.now(timezone.utc).isoformat(),'sha256':sha256(body),'bytes':len(body),'final_url':metadata['url'],'url':job['url']}
 a.write_text(json.dumps(record,indent=2)+'\n')
 return {'id':job['id'],'status':record['status'],'bytes':len(body)}
with ThreadPoolExecutor(max_workers=2) as pool:
 for result in pool.map(fetch,jobs):print(json.dumps(result),flush=True)
