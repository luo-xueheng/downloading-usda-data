"""Full-backfill gates never replace incomplete production coverage with samples."""
from collections import Counter
from pathlib import Path
import json
import pytest
from usda_data.storage import hash_file

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/acceptance/phase-09'

def evidence(name):
    path=OUT/name
    assert path.exists(),f'Missing required full-backfill evidence: {name}'
    return json.loads(path.read_text())

@pytest.mark.acceptance('P09-A1')
def test_required_inventory_has_no_unresolved_partitions():
    result=evidence('coverage_reconciliation.json')
    assert result['expected']==result['succeeded']+result['source_unavailable']
    assert result['unresolved']==0

@pytest.mark.acceptance('P09-A2')
def test_every_full_export_validated():
    result=evidence('full_validation.json')
    assert result['passed']==result['expected_tasks']
    assert result['failed']==result['blocked']==0
    assert all(r['duplicate_keys']==r['missing_required_dimensions']==0 for r in result['checks'])
    assert evidence('source_accounting.json')['status']=='pass'
    aggregates=evidence('aggregate_validation.json')
    assert len(aggregates)==7 and all(r['status']=='pass' for r in aggregates)

@pytest.mark.acceptance('P09-A3')
def test_frozen_independent_audits_and_complete_export_linkage():
    result=evidence('independent_audit.json')
    assert result['checks']>=140
    assert result['counts'].get('fail',0)==0
    assert len(result['per_dataset'])==7
    assert all(r.get('pass',0)>=20 for r in result['per_dataset'].values())
    assert result['report_export_linkage']=='verified', 'Report parser references pass only after exact complete-export linkage is also verified'

@pytest.mark.acceptance('P09-A4')
def test_source_coverage_boundaries_and_gaps_reconciled():
    result=evidence('coverage_reconciliation.json')
    assert result['unresolved']==0
    assert result['coverage_boundaries_verified'] is True
    assert result['historical_vintages_note']
    assert evidence('source_accounting.json')['boundaries']['psd']['verified_partitions']==628
    assert evidence('wasde_gap_evidence.json')['status']=='pass'

@pytest.mark.acceptance('P09-A5')
def test_full_manifest_and_real_subset_resume():
    trial=evidence('subset_resume.json')
    assert trial['unchanged'] and trial['resume_equal_to_clean'] and trial['partial_exit_code']==1
    manifest=ROOT/'data/exports/complete.latest.json'
    assert manifest.exists(),'No complete seven-dataset export selected'
    selection=json.loads(manifest.read_text())
    assert {r['dataset'] for r in selection['exports'].values()}=={'wasde','costs-returns','export-sales','world-production','grain-trade','oilseed-trade','rma-sob'}
    assert selection['status']=='complete'
    for r in selection['exports'].values():
        assert hash_file(ROOT/'data/exports'/r['csv_path'])==r['csv_sha256']
        assert r['snapshot_ids'] or r['rows']==0

@pytest.mark.acceptance('P09-A6')
def test_full_validation_memory_and_small_chunk_invariance():
    result=evidence('full_validation.json');trial=evidence('subset_resume.json')
    budget=json.loads((ROOT/'config/full_backfill.json').read_text())['memory_budget_mib']
    assert result['peak_rss_mib']<=budget
    assert trial['small_chunk_equal'] and trial['small_chunk_size']<trial['default_chunk_size']
    reports=evidence('report_backfill_summary.json')
    assert reports['peak_rss_mib']<=budget
    export_memory=evidence('full_export_memory.json')
    assert export_memory['peak_rss_mib']<=budget and export_memory['hashes_match_original_full_run'] is True

@pytest.mark.acceptance('P09-A7')
def test_all_report_candidates_and_table_maps():
    result=evidence('report_backfill_summary.json')
    assert result['expected']==606
    assert evidence('report_layout_inventory.json')['unresolved_available_tables']==0
    assert result['failed']==0 and result['succeeded']==result['expected']
    records=[json.loads(p.read_text()) for p in (OUT/'report_partitions').glob('*.json')]
    assert len(records)==606
    for r in records:
        assert r['parser_source_hash']==result['parser_source_hash']
        assert r['status'] in {'succeeded','source_unavailable'}
        assert hash_file(ROOT/'data'/r['csv_path'])==r['csv_sha256']
        coverage=json.loads((ROOT/'data'/r['coverage_path']).read_text())
        assert coverage['input_cells']==r['input_cells']
        assert coverage.get('source_unavailable') or coverage['tables']

@pytest.mark.acceptance('P09-A3')
def test_additional_references_are_distinct_from_development_cells():
    numeric=json.loads((ROOT/'tests/fixtures/phase_09/numeric_audit_references.json').read_text())['references']
    numeric+=json.loads((ROOT/'tests/fixtures/phase_09/numeric_audit_supplement.json').read_text())['references']
    def identity(ref,dataset,new):
        artifact=ref['source_artifact_id'] if new else ref['sha256']
        locator=ref['source_locator'] if new else ref['locator']
        if dataset=='wasde':return artifact,locator['csv_record_including_header']
        if dataset=='costs-returns':return artifact,locator['csv_record_including_header'] if new else locator.get('record')
        if dataset=='export-sales':return artifact,locator['array_index'],locator['field']
        return artifact,locator['line'],locator['field_1_based']
    for dataset,phase in [('wasde','02'),('costs-returns','03'),('export-sales','04'),('rma-sob','07')]:
        old=json.loads((ROOT/f'tests/fixtures/phase_{phase}/references.json').read_text())
        previous={identity(r,dataset,False) for r in old}
        extra={identity(r,dataset,True) for r in numeric if r['dataset']==dataset}
        assert len(extra)>=20 and not extra&previous
    old=json.loads((ROOT/'tests/fixtures/phase_06/references.json').read_text())
    new=json.loads((ROOT/'tests/fixtures/phase_09/report_audit_references.json').read_text())
    dimensions=['table_title','row_label','indicator','comparison_label']
    previous={(r['sha256'],*(r[k] for k in dimensions)) for r in old}
    extra={(r['sha256'],*(r[k] for k in dimensions)) for r in new}
    assert not extra&previous
