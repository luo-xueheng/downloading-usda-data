"""Import selected full exports into isolated local SQLite and prove exact readback."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import resource
import sys
import time
from usda_data.schema import Schema
from usda_data.sql import connect, import_csv, readback_hash, check_constraints, quote
from usda_data.storage import hash_file, atomic_write, canonical


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', default='data/exports/datasets')
    parser.add_argument('--database', required=True, help='New isolated local SQLite file; existing files are rejected')
    parser.add_argument('--output', required=True)
    parser.add_argument('--chunk-size', type=int, default=5000)
    args = parser.parse_args()
    root = Path(args.input_dir)
    path = Path(args.database)
    if path.exists():
        parser.error('Use a new database path; existing files are never overwritten')
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = root/'complete.latest.json'
    manifest = json.loads(manifest_path.read_text())
    assert manifest['status'] == 'complete'
    results = []
    started = datetime.now(timezone.utc).isoformat()
    with connect(path) as db:
        db.execute('PRAGMA cache_size=-16384')
        for dataset, export in sorted(manifest['exports'].items()):
            tick = time.monotonic()
            csv_path = root/export['csv_path']
            assert hash_file(csv_path) == export['csv_sha256']
            schema_path = root/export['schema_path']
            schema = Schema.load(schema_path)
            count = import_csv(db, dataset, schema, csv_path, chunk_size=args.chunk_size)
            result = readback_hash(db, dataset, schema, chunk_size=args.chunk_size)
            assert count == result['rows'] == export['rows']
            assert result['csv_sha256'] == export['csv_sha256']
            constraints = check_constraints(db, dataset, schema)
            results.append({'dataset': dataset, 'schema': schema.name, 'version': schema.version,
                            'schema_sha256': hash_file(schema_path), **result, **constraints,
                            'status': 'pass', 'elapsed_seconds': time.monotonic()-tick})
            atomic_write(Path(args.output), canonical({'status': 'in_progress', 'checks': results}))
            print(dataset, count, 'exact SQL readback passed', flush=True)
    summary = {'status': 'pass', 'started_at_utc': started, 'completed_at_utc': datetime.now(timezone.utc).isoformat(),
               'input_manifest_sha256': hash_file(manifest_path), 'database': str(path),
               'strategy': 'Exact Decimal TEXT; composite business keys; exact_decimal collation; null and typed column constraints',
               'rows': sum(r['rows'] for r in results), 'checks': results,
               'peak_rss_mib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1024*1024 if sys.platform=='darwin' else 1024)}
    atomic_write(Path(args.output), canonical(summary))
    print(json.dumps({k:v for k,v in summary.items() if k!='checks'}, indent=2))


if __name__ == '__main__':
    main()
