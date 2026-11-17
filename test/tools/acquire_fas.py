"""Acquire reviewed FAS ESR dictionary/partition fixtures, never authentication data."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys
ROOT=Path(__file__).resolve().parents[2]
from usda_data.credentials import load_api_key
from usda_data.http import HTTPClient
from usda_data.config import HTTPConfig
from usda_data.errors import USDAError
from usda_data.storage import sha256
key=load_api_key()
phase=sys.argv[1]
if phase not in {'05','06'}:raise ValueError('Unsupported acquisition phase')
target=ROOT/'test/fixtures'/f'phase_{phase}'
target.mkdir(parents=True,exist_ok=True)
endpoints=json.loads(Path(sys.argv[2]).read_text())
results=[]
with HTTPClient(HTTPConfig(max_attempts=3,trust_environment=False)) as client:
 for endpoint in endpoints:
  url='https://api.fas.usda.gov'+endpoint['path']
  record={'id':endpoint['id'],'url':url,'checked_at_utc':datetime.now(timezone.utc).isoformat()}
  try:
   body,metadata=client.get(url,expected='json',headers={'X-Api-Key':key,'Accept':'application/json'})
   assert key.encode() not in body, 'Source response contained a credential; not archived'
   payload=json.loads(body);record.update(metadata,sha256=sha256(body),bytes=len(body),record_count=len(payload) if isinstance(payload,list) else None)
   p=target/(endpoint['id']+'.json')
   if p.exists() and p.read_bytes()!=body:raise ValueError('Refusing to overwrite frozen source response')
   p.write_bytes(body);Path(str(p)+'.acquisition.json').write_text(json.dumps(record,indent=2)+'\n')
  except USDAError as exc:
   record.update(status='blocked',error_type=type(exc).__name__,error=str(exc))
  results.append(record);print(json.dumps(record),flush=True)
report=ROOT/f'.cache/acquisition/phase-{phase}'/('acquisition-'+datetime.now(timezone.utc).strftime('%H%M%S')+'.json')
report.parent.mkdir(parents=True,exist_ok=True)
report.write_text(json.dumps(results,indent=2)+'\n')
raise SystemExit(0 if all(r['status']==200 for r in results) else 1)
