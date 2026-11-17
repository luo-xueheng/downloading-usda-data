"""Acquire an explicit reviewed public-source job list through the bounded HTTP client."""
import argparse,json
from pathlib import Path
from datetime import datetime,timezone
from usda_data.http import HTTPClient
from usda_data.config import HTTPConfig
from usda_data.storage import sha256
from usda_data.errors import USDAError

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('jobs',type=Path);parser.add_argument('--direct',action='store_true')
args=parser.parse_args();failed=False
with HTTPClient(HTTPConfig(trust_environment=not args.direct)) as client:
 for job in json.loads(args.jobs.read_text()):
  record={**job,'checked_at_utc':datetime.now(timezone.utc).isoformat()}
  try:
   body,meta=client.get(job['url'],expected=job['format'])
   record.update(meta,sha256=sha256(body),bytes=len(body),final_url=meta['url'],url=job['url'])
   path=Path(job['path']);path.parent.mkdir(parents=True,exist_ok=True)
   if path.exists() and path.read_bytes()!=body:raise ValueError('Refusing to overwrite frozen source bytes')
   path.write_bytes(body);Path(str(path)+'.acquisition.json').write_text(json.dumps(record,indent=2)+'\n')
  except USDAError as e:
   record.update(status='blocked',error_type=type(e).__name__,error=str(e));failed=True
  print(json.dumps(record),flush=True)
raise SystemExit(1 if failed else 0)
