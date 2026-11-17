"""Final handover gates, with real evidence separate from synthetic edge tests."""
from decimal import Decimal
from pathlib import Path
import json
import sqlite3
import xml.etree.ElementTree as ET
import pytest
from usda_data.cli import main
from usda_data.errors import AuthenticationError, DownloadError, ConfigurationError
from usda_data.schema import Schema, Field
from usda_data.sql import connect, import_csv, readback_hash, check_constraints
from usda_data.storage import hash_file

import os
ROOT=Path(os.environ.get('USDA_ARCHIVE_ROOT', '/nonexistent/usda-archive'))
OUT = ROOT/'artifacts/acceptance/phase-10'


def evidence(name):
    path = OUT/name
    assert path.exists(), f'Missing Phase 10 evidence: {name}'
    return json.loads(path.read_text())


@pytest.mark.acceptance('P10-A1')
def test_clean_wheel_install_and_documented_examples():
    install = evidence('clean-install.command.json')
    assert install['exit_code'] == 0
    clean = evidence('clean_environment.json')
    assert clean['system_site_packages'] is False
    assert clean['editable'] is False
    assert '/site-packages/usda_data/' in clean['module_file']
    assert evidence('readme-examples.command.json')['exit_code'] == 0
    assert evidence('examples/checks.json')['status'] == 'pass'
    assert evidence('readme_cli_checks.json')['status'] == 'pass'


@pytest.mark.acceptance('P10-A2')
def test_all_seven_installed_interfaces():
    from usda_data.config import DATASETS
    checks = evidence('examples/checks.json')['checks']
    assert {r['dataset'] for r in checks} == set(DATASETS)
    assert all(r['status'] == 'pass' and r['rows'] > 0 and r['exit_code'] == 0 for r in checks)


@pytest.mark.acceptance('P10-A3')
def test_all_full_export_sql_roundtrips():
    result = evidence('sql_roundtrip.json')
    manifest = ROOT/'data/exports/datasets/complete.latest.json'
    assert result['status'] == 'pass' and len(result['checks']) == 7
    assert result['input_manifest_sha256'] == hash_file(manifest)
    exports = json.loads(manifest.read_text())['exports']
    for check in result['checks']:
        export = exports[check['dataset']]
        assert check['rows'] == export['rows']
        assert check['csv_sha256'] == export['csv_sha256']
        assert check['schema_sha256'] == hash_file(manifest.parent/export['schema_path'])
    assert result['rows'] == sum(v['rows'] for v in exports.values())


@pytest.mark.acceptance('P10-A4')
def test_every_schema_constraint_proof():
    result = evidence('sql_roundtrip.json')
    manifest = json.loads((ROOT/'data/exports/datasets/complete.latest.json').read_text())
    for check in result['checks']:
        schema = Schema.load(ROOT/'data/exports/datasets'/manifest['exports'][check['dataset']]['schema_path'])
        assert check['duplicate_rejected'] is True
        assert set(check['missing_fields_rejected']) == {f.name for f in schema.fields if f.key or not f.nullable}










@pytest.mark.acceptance('P10-A6')
def test_all_prior_suites_and_required_live_evidence():
    # The full final suite includes this file; use the separate prior-suite run
    # here to avoid a self-referential result. Final completion also checks it.
    assert evidence('baseline-offline.command.json')['exit_code'] == 0
    assert evidence('required-live.command.json')['exit_code'] == 0
    tree = ET.parse(OUT/'required-live.xml')
    cases = tree.findall('.//testcase')
    assert len(cases) == 9
    assert not tree.findall('.//failure') and not tree.findall('.//error') and not tree.findall('.//skipped')
    assert evidence('phase00-offline.command.json')['exit_code'] == 0
    assert evidence('verifier-tests.command.json')['exit_code'] == 0
    for phase in range(10):
        path = ROOT/f'artifacts/acceptance/phase-{phase:02}/results.json'
        values = json.loads(path.read_text())
        if isinstance(values,dict):
            values = values['results']
        assert values and all(v['status']=='pass' for v in values)
    live = evidence('phase-00-direct/live_checks.json')
    blocked = [r for r in live if r['status'] != 'pass']
    if blocked:
        # A skipped required check is deliberately BLOCKED by the acceptance
        # recorder. It must never be promoted to pass or replaced by cached data.
        assert all(r['status'] == 'blocked' for r in blocked)
        pytest.skip('Required Phase 00 live recheck externally blocked: ' + ', '.join(f"{r['id']} HTTP {r.get('http_status')}" for r in blocked))
    assert evidence('phase00-live-direct.command.json')['exit_code'] == 0


@pytest.mark.acceptance('P10-A7')
def test_handover_manifest_and_schema_agreement():
    final = evidence('final_dataset_manifest.json')
    original = json.loads((ROOT/'data/exports/datasets/complete.latest.json').read_text())
    assert final == original
    registry = evidence('handover_index.json')
    assert registry['unresolved_required_coverage'] == 0
    assert len(registry['datasets']) == 7
    for entry in registry['datasets']:
        export = original['exports'][entry['dataset']]
        assert entry['rows'] == export['rows'] and entry['csv_sha256'] == export['csv_sha256']
        sidecar = ROOT/'data/exports/datasets'/export['schema_path']
        assert json.loads(sidecar.read_text()) == json.loads((ROOT/entry['schema']).read_text())
    for path in registry['required_documents']:
        assert (ROOT/path).is_file()
    assert 'Phase 10 handover remains gated' not in (ROOT/'README.md').read_text()
    assert 'Only WASDE is currently implemented' not in (ROOT/'src/usda_data/api.py').read_text()


@pytest.mark.acceptance('P10-A3')
@pytest.mark.parametrize('kind',['psd','report'])
def test_ancillary_business_schemas_sql(tmp_path,kind):
    if kind == 'psd':
        root = ROOT/'artifacts/acceptance/phase-05/sample/exports'
        manifest = json.loads((root/'psd.latest.json').read_text())
        schema = Schema.load(root/manifest['schema_path'])
        path = root/manifest['csv_path']
    else:
        schema = Schema.load(ROOT/'schemas/fas_report_observations.v1.json')
        path = next((OUT/'examples/data/normalized/world-production-reports').rglob('data.csv'))
    with connect(':memory:') as db:
        rows = import_csv(db,kind,schema,path,chunk_size=37)
        assert rows > 0
        assert readback_hash(db,kind,schema)['csv_sha256'] == hash_file(path)
        assert check_constraints(db,kind,schema)['duplicate_rejected']

pytestmark = pytest.mark.historical
