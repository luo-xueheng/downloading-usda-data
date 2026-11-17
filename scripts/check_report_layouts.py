"""Recheck cached original reports without network access or export publication."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import traceback
from usda_data.sources.report_tables import parse_report
from usda_data.sources.reports import resolve_attachment
from usda_data.errors import DownloadError
from usda_data.storage import Store, atomic_write, canonical, sha256

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--names', nargs='*')
    parser.add_argument('--failed-only', action='store_true')
    args = parser.parse_args()
    evidence = ROOT / 'artifacts/acceptance/phase-09'
    store = Store(ROOT / 'data')
    output = evidence / 'resume/layout_checks'
    output.mkdir(parents=True, exist_ok=True)
    version = sha256((ROOT / 'src/usda_data/sources/report_tables.py').read_bytes())
    files = sorted((evidence / 'report_partitions').glob('*.json'))
    totals = Counter()
    for path in files:
        if args.names and path.stem not in args.names:
            continue
        source = json.loads(path.read_text())
        if args.failed_only and source['status'] != 'failed':
            continue
        if not source.get('source_artifact_id') and not (store.root/'manifests/reports/resolved'/f'{sha256(source["url"].encode())}.json').exists():
            continue
        target = output / path.name
        if target.exists():
            old = json.loads(target.read_text())
            if old['parser_source_hash'] == version:
                totals[old['status']] += 1
                continue
        result = {'family': source['family'], 'period': source['report_period'],
                  'source_artifact_id': source.get('source_artifact_id'),
                  'parser_source_hash': version, 'checked_at_utc': datetime.now(timezone.utc).isoformat()}
        try:
            class Offline:
                def get(self,*a,**kw):raise DownloadError('Uncached source; offline verification cannot download')
            body,receipt,resolved=resolve_attachment(Offline(),store,{'report_family':source['family'],'report_period':source['report_period'],'url':source['url']})
            result['source_artifact_id']=receipt['source_artifact_id']
            frame, accounting = parse_report(body, source['family'], receipt, expected_period=source['report_period'])
            result.update(status='pass', rows=len(frame), input_cells=accounting['input_cells'], tables=len(accounting['tables']))
        except Exception as exc:
            result.update(status='fail', error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())
        atomic_write(target, canonical(result))
        totals[result['status']] += 1
        print(path.stem, result['status'], result.get('error', result.get('rows')), flush=True)
    print(dict(totals), flush=True)
    return int(bool(totals['fail']))

if __name__ == '__main__':
    raise SystemExit(main())
