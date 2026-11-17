"""Validate shipped examples and complete-run export publication."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import pytest
from usda_data.config import DATASETS
from usda_data.schema import Schema
from usda_data.storage import hash_file, canonical

ROOT = Path(__file__).resolve().parents[2]


def test_seven_examples_preserve_schema_and_both_report_sources():
    manifest = json.loads((ROOT / 'examples/manifest.json').read_text())
    assert {entry['dataset'] for entry in manifest['examples']} == set(DATASETS)
    assert len(list((ROOT / 'examples').glob('*.csv'))) == 7
    for entry in manifest['examples']:
        path = ROOT / 'examples' / entry['file']
        schema = Schema.load(ROOT / entry['schema'])
        assert hash_file(path) == entry['csv_sha256']
        frame = schema.read_csv(path)
        assert len(frame) == entry['rows'] == 200
        assert schema.csv_bytes(frame) == path.read_bytes()
        assert entry['is_excerpt'] and entry['rows'] < entry['request_rows']
        if 'observation_kind' in frame:
            assert frame['observation_kind'].value_counts().to_dict() == {'psd_current': 100, 'report_table': 100}


@pytest.mark.parametrize("current_rma", [False, True])
def test_aggregate_current_schemas_and_reject_corruption(tmp_path, current_rma):
    """Real typed sample CSVs must aggregate; a corrupt input cannot replace selection."""
    sample = json.loads((ROOT / 'examples/manifest.json').read_text())
    source = tmp_path / 'input'
    source.mkdir()
    exports = {}
    for entry in sample['examples']:
        folder = source / entry['dataset']
        folder.mkdir()
        (folder / 'data.csv').write_bytes((ROOT / 'examples' / entry['file']).read_bytes())
        schema_path = 'schemas/rma_sob.v3.json' if current_rma and entry['dataset'] == 'rma-sob' else entry['schema']
        schema = Schema.load(ROOT / schema_path)
        (folder / 'schema.json').write_bytes(canonical(schema.to_dict()))
        exports[entry['dataset']] = {
            'dataset': entry['dataset'], 'rows': entry['rows'],
            'csv_path': f'{entry["dataset"]}/data.csv', 'schema_path': f'{entry["dataset"]}/schema.json',
            'csv_sha256': entry['csv_sha256'], 'snapshot_ids': entry['source_snapshot_ids'],
        }
    manifest = {'status': 'complete', 'run_id': 'sample-validation', 'configuration_hash': 'test', 'exports': exports}
    (source / 'complete.latest.json').write_bytes(canonical(manifest))
    output = tmp_path / 'output'
    command = [sys.executable, str(ROOT / 'scripts/aggregate_exports.py'), '--input-dir', str(source), '--output-dir', str(output)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    before = (output / 'complete.latest.json').read_bytes()
    selected = json.loads(before)
    assert set(selected['exports']) == set(DATASETS)
    for dataset, entry in selected['exports'].items():
        assert hash_file(output / entry['csv_path']) == exports[dataset]['csv_sha256']
    (source / 'rma-sob/data.csv').write_bytes(b'corrupted source')
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0
    assert (output / 'complete.latest.json').read_bytes() == before


def test_failed_example_download_preserves_existing_csv(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('download_example', ROOT / 'scripts/download_example.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = tmp_path / 'sample.csv'
    output.write_bytes(b'previous successful sample\n')
    monkeypatch.setattr(module, 'fetch', lambda args: 1)
    assert module.main(['--dataset', 'wasde', '--example-output', str(output), '--start', '2026-11-10', '--end', '2026-11-10']) == 1
    assert output.read_bytes() == b'previous successful sample\n'
