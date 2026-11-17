"""Assemble auditable handover links and schema dictionaries without asserting a pass."""
import json
from pathlib import Path
from usda_data.storage import hash_file, atomic_write, canonical

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/acceptance/phase-10'


def main():
    manifest = ROOT/'data/exports/datasets/complete.latest.json'
    selected = json.loads(manifest.read_text())
    atomic_write(OUT/'final_dataset_manifest.json', manifest.read_bytes())
    datasets = []
    schemas = {}
    for dataset, export in selected['exports'].items():
        sidecar = manifest.parent/export['schema_path']
        schema = json.loads(sidecar.read_text())
        name = f'schemas/{schema["name"]}.v{schema["version"]}.json'
        assert json.loads((ROOT/name).read_text()) == schema
        schemas[name] = schema
        datasets.append({'dataset': dataset, 'rows': export['rows'], 'csv_sha256': export['csv_sha256'], 'schema': name, 'schema_sha256': hash_file(sidecar), 'csv_path': str((manifest.parent/export['csv_path']).relative_to(ROOT))})
    # Ancillary public outputs also have documented business schemas.
    for name in ['schemas/psd_observations.v1.json','schemas/fas_report_observations.v1.json']:
        schemas[name] = json.loads((ROOT/name).read_text())
    def cell(value):
        return str(value).replace('|','\\|').replace('\n',' ')
    lines = ['# Current business-table field dictionary', '', 'Generated from the versioned schema contracts. Earlier schema versions remain available for earlier snapshots; the selected export sidecar always governs a file.', '']
    for name, schema in sorted(schemas.items()):
        lines += [f'## {schema["name"]} version {schema["version"]}', '', f'Machine-readable contract: `{name}`. CSV null token: `\\N`; literal leading backslashes are escaped.', '', '| Field | Type | Nullable | Business key | Meaning | Source mapping | Unit | Missing rule |', '|---|---|---|---|---|---|---|---|']
        for f in schema['fields']:
            lines.append('| '+' | '.join(cell(f.get(key,'')) for key in ['name','type','nullable','key','meaning','source_mapping','unit','missing_rule'])+' |')
        lines.append('')
    (ROOT/'docs/field_dictionary.md').write_text('\n'.join(lines)+'\n')
    documents = ['README.md','docs/interfaces.md','docs/sql_transfer.md','docs/release_notes.md','docs/handover.md','docs/field_dictionary.md','docs/acceptance_index.md','docs/execution_status.md','docs/source_registry.md','docs/credential_setup.md','docs/updates_and_recovery.md','docs/backfill.md']
    documents += [f'docs/{name}.md' for name in ['wasde','export_sales','costs_returns','rma_sob','world_production','grain_trade','oilseed_trade','psd','reports']]
    coverage = json.loads((ROOT/'artifacts/acceptance/phase-09/coverage_reconciliation.json').read_text())
    index = {'cutoff': '2026-11-16', 'manifest_sha256': hash_file(manifest), 'datasets': datasets, 'required_documents': documents, 'unresolved_required_coverage': coverage['unresolved'], 'expected_coverage_records': coverage['expected'], 'source_unavailable_records': coverage['source_unavailable'], 'prior_phase_results': [f'artifacts/acceptance/phase-{i:02}/results.json' for i in range(10)], 'final_phase_results': 'artifacts/acceptance/phase-10/results.json', 'source_limitations': ['WASDE structured coverage before April 2010 unsupported','Evidenced report nonpublication and June 2016 WAP Table 10 source omission','Current-revised API observations do not provide historical publication vintages','ESR API synchronization and RMA bulk ZIP synchronization remain unknown']}
    atomic_write(OUT/'handover_index.json', canonical(index))
    lines = ['# Acceptance evidence index', '', 'The execution ledger is the authoritative phase status. Historical phase results retain their original source-tree/configuration identities. Final suites re-exercise the mandatory tests at handover; they do not rewrite past acceptance hashes.', '', '| Phase | Evidence | Machine-readable results |', '|---|---|---|']
    for i in range(11):
        path = f'../artifacts/acceptance/phase-{i:02}'
        lines.append(f'| {i:02} | [Summary]({path}/summary.md) | [Results]({path}/results.json) |')
    lines += ['', '## Final handover evidence', '', '- `artifacts/acceptance/phase-10/commands.txt`: exact invocations, working directory and exit codes.', '- `clean_environment.json`, `clean-install.txt`, `final-wheel-install.txt`, `requirements-tested.txt`: isolated wheel installation and resolved dependency versions.', '- `examples/checks.json`: seven installed Python/CLI comparisons, with command arguments and hashes.', '- `sql_roundtrip.json`: all complete rows, source/export hashes, schema hashes and SQL constraint rejection checks.', '- `required-live.xml` and `required-live.txt`: all nine required adapter live tests, with no skipped tests.', '- `phase-00/` and `phase-00-direct/`: independent standard-library inventory, public access and reference verifier.', '- `all-offline.xml`: complete final offline suite, including Phase 10.', '- `final_dataset_manifest.json` and `handover_index.json`: selected data and documentation coverage.', '- `source_checks.csv`: explicit reference to existing independent numeric accuracy evidence; no new numerical truth is inferred from roundtrip equality.', '', 'The initial SQL constraint failure and RMA HTTP 502 probes are retained separately. Later passing evidence must actually rerun the affected checks. No failed or skipped run is counted as a pass.', '']
    (ROOT/'docs/acceptance_index.md').write_text('\n'.join(lines))
    (OUT/'source_checks.csv').write_text('check_id,status,scope,evidence\nP10-transfer,not_applicable,"No new independent source numeric claims; exact interface and SQL preservation checks only",artifacts/acceptance/phase-10/sql_roundtrip.json\nP09-numeric,pass,"164 independently checked source cells across seven datasets",artifacts/acceptance/phase-09/source_checks.csv\n')


if __name__ == '__main__':
    main()
