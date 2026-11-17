"""Bounded read-only diagnostics; no response bodies or authentication values logged."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,httpx
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from fas_credentials import load_api_key
key=load_api_key();url='https://api.fas.usda.gov/api/esr/commodities';results=[]
for environment_proxy,authenticate in [(True,False),(True,True),(False,True)]:
 record={'url':url,'environment_proxy':environment_proxy,'authenticated_request':authenticate,'checked_at_utc':datetime.now(timezone.utc).isoformat()}
 try:
  with httpx.Client(timeout=15,trust_env=environment_proxy,follow_redirects=False) as client:
   response=client.get(url,headers={'X-Api-Key':key,'Accept':'application/json'} if authenticate else {'Accept':'application/json'})
   record.update(http_status=response.status_code,content_type=response.headers.get('content-type'),bytes=len(response.content))
   try:record['json_type']=type(response.json()).__name__
   except ValueError:record['json_type']=None
 except httpx.HTTPError as exc:record.update(http_status=None,error_type=type(exc).__name__)
 results.append(record);print(json.dumps(record),flush=True)
(ROOT/'artifacts/acceptance/phase-04/access_diagnostics.json').write_text(json.dumps(results,indent=2)+'\n')
