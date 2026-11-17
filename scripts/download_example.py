"""Download a bounded request and save a documented CSV excerpt of its final output."""
import argparse
import json
from pathlib import Path
import shlex
import tempfile
import sys
from datetime import datetime, timezone
import pandas as pd
from usda_data.cli import main as fetch
from usda_data.config import DATASETS
from usda_data.schema import Schema
from usda_data.storage import atomic_write, canonical, hash_file


def sample_export(root, manifest, row_limit):
    """Keep both PSD and report rows when the dataset combines the two sources."""
    schema = Schema.load(root / manifest['schema_path'])
    combined = 'observation_kind' in {field.name for field in schema.fields}
    limits = {'psd_current': (row_limit + 1) // 2, 'report_table': row_limit // 2} if combined else {'all': row_limit}
    counts = dict.fromkeys(limits, 0)
    selected = []
    for chunk in schema.read_csv_chunks(root / manifest['csv_path'], chunk_size=5000):
        for kind, limit in limits.items():
            available = chunk[chunk['observation_kind'] == kind] if combined else chunk
            chosen = available.iloc[:max(0, limit - counts[kind])]
            if len(chosen):
                selected.append(chosen)
                counts[kind] += len(chosen)
        if all(counts[kind] >= limit for kind, limit in limits.items()):
            break
    frame = pd.concat(selected, ignore_index=True) if selected else schema.frame([])
    return schema, frame


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--dataset', required=True, choices=DATASETS)
    parser.add_argument('--example-output', type=Path, required=True)
    parser.add_argument('--rows', type=int, default=200)
    argv = list(sys.argv[1:] if argv is None else argv)
    args, options = parser.parse_known_args(argv)
    if args.rows < 2:
        parser.error('--rows must be at least 2')
    if any(option.split('=')[0] == '--output-dir' for option in options):
        parser.error('Use --example-output; full export staging is managed automatically')
    index_path = args.example_output.parent / 'manifest.json'
    index = json.loads(index_path.read_text()) if index_path.exists() else {'schema_version': 1, 'examples': []}
    if not isinstance(index.get('examples'), list):
        parser.error('Existing example manifest must contain an examples list')
    # Finish the entire selected request before publishing any example.
    with tempfile.TemporaryDirectory(prefix='usda-example-') as temporary:
        output = Path(temporary)
        command = ['fetch', '--dataset', args.dataset, *options, '--output-dir', str(output)]
        status = fetch(command)
        if status:
            return status
        manifest = json.loads((output / f'{args.dataset}.latest.json').read_text())
        schema, frame = sample_export(output, manifest, args.rows)
        atomic_write(args.example_output, schema.csv_bytes(frame))
        metadata = {
            'dataset': args.dataset,
            'file': args.example_output.name,
            'command': shlex.join(['.venv/bin/python', 'scripts/download_example.py', *argv]),
            'generated_at_utc': datetime.now(timezone.utc).isoformat(),
            'generation_mode': 'Download pipeline with cache reuse; missing sources may be fetched from the network',
            'rows': len(frame),
            'request_rows': manifest['rows'],
            'is_excerpt': len(frame) < manifest['rows'],
            'selection': 'First rows per observation_kind (PSD/report)' if 'observation_kind' in frame else 'First rows in final export order',
            'schema': f'schemas/{schema.name}.v{schema.version}.json',
            'csv_sha256': hash_file(args.example_output),
            'request_csv_sha256': manifest['csv_sha256'],
            'fetch_command': shlex.join(['python', '-m', 'usda_data', 'fetch', '--dataset', args.dataset, *options]),
            'source_snapshot_ids': sorted(set(frame['snapshot_id'])) if len(frame) else [],
        }
        index['examples'] = [entry for entry in index['examples'] if entry['dataset'] != args.dataset] + [metadata]
        index.pop('generated_from', None)
        index.pop('generated_at_utc', None)
        atomic_write(index_path, canonical(index))
        print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
