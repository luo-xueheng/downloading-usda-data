#!/usr/bin/env python3
"""Acquire an explicitly reviewed list of public Phase 00 evidence URLs.

No recursive crawling, API credentials, normalization, or production writes.
"""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def acquire(job):
    record = dict(job, checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    try:
        request = urllib.request.Request(job['url'], headers={'User-Agent': 'Mozilla/5.0 (compatible; USDA-source-verification/1.0)'})
        with urllib.request.urlopen(request, timeout=55) as response:
            body = response.read(80_000_001)
            if len(body) > 80_000_000:
                raise ValueError('Evidence exceeds 80 MB limit')
            record.update(status=response.status, final_url=response.url,
                          content_type=response.headers.get('Content-Type'),
                          last_modified=response.headers.get('Last-Modified'))
    except urllib.error.HTTPError as exc:
        body = exc.read()
        record.update(status=exc.code, final_url=exc.url, error=f'HTTP {exc.code}')
    except Exception as exc:
        record.update(status=None, error=str(exc))
        body = b''
    target = ROOT / job['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() != body:
        raise ValueError(f'Refusing to overwrite frozen bytes: {target}')
    target.write_bytes(body)
    record.update(sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
    target.with_suffix(target.suffix + '.acquisition.json').write_text(json.dumps(record, indent=2) + '\n')
    return record

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('jobs', type=Path)
    args = parser.parse_args()
    jobs = json.loads(args.jobs.read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for item in pool.map(acquire, jobs):
            print(json.dumps(item))

if __name__ == '__main__':
    main()
