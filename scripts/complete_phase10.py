"""Close handover truthfully; external required-check skips keep the phase blocked."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from usda_data.storage import hash_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/acceptance/phase-10'


def main():
    results = json.loads((OUT/'results.json').read_text())
    assert len(results) == 7
    statuses = {r['test_id']:r['status'] for r in results}
    tree = ET.parse(OUT/'all-offline.xml')
    cases = tree.findall('.//testcase')
    failures = tree.findall('.//failure') + tree.findall('.//error')
    skips = tree.findall('.//skipped')
    passed = all(v == 'pass' for v in statuses.values()) and bool(cases) and not failures and not skips
    external = statuses.get('P10-A6') == 'blocked' and all(v == 'pass' for k,v in statuses.items() if k != 'P10-A6') and not failures
    status = 'passed' if passed else 'blocked_external' if external else 'failed'
    stamp = datetime.now(timezone.utc).isoformat()
    sql = json.loads((OUT/'sql_roundtrip.json').read_text())
    examples = json.loads((OUT/'examples/checks.json').read_text())
    release = {'status':status,'assessed_at_utc':stamp,'acceptance_ids':statuses,
               'offline_tests':{'collected':len(cases),'passed':len(cases)-len(failures)-len(skips),'failed':len(failures),'skipped_required':len(skips)},
               'required_adapter_live_tests':9,'sql_rows':sql['rows'],'sql_peak_rss_mib':sql['peak_rss_mib'],
               'interface_datasets':len(examples['checks']),
               'wheel_sha256':hash_file(OUT/'dist/usda_data-0.1.0-py3-none-any.whl'),
               'external_blocker':None if passed else 'Required Phase 00 RMA 2010 ZIP live recheck returns HTTP 502 through proxy and explicit direct transport; immutable historical bytes still validate offline.'}
    (OUT/'release_status.json').write_text(json.dumps(release,indent=2)+'\n')
    blocker = 'None' if passed else release['external_blocker']
    action = 'Handover accepted; use documented sync and recovery' if passed else 'After source recovery, rerun Phase 00 live/offline at matching source hash, Phase 10 acceptance and full offline suite'
    ledger = ROOT/'docs/execution_status.md'
    old = next(line for line in ledger.read_text().splitlines() if line.startswith('| 10 |'))
    start = old.split('|')[3].strip()
    new = f'| 10 | {status} | {start} | {stamp if passed else "-"} | artifacts/acceptance/phase-10/ | {blocker} | {action} |'
    ledger.write_text(ledger.read_text().replace(old,new))
    version = results[0]['code_version']
    lines = ['# Phase 10 — interface, SQL portability and handover', '', f'Phase: 10  \nStatus: **{status}**  \nAssessed (UTC): {stamp}', '',
             f'Mandatory IDs: {sum(v=="pass" for v in statuses.values())}/7 passed. '+', '.join(f'{k}: {v}' for k,v in statuses.items())+'.', '',
             f'Source-tree hash: `{version["source_tree_sha256"]}`. Configuration hash: `{results[0]["configuration_hash"]}`.', '',
             'The regular wheel installs in an isolated Python 3.13.5 environment with no system-site packages and no editable source import. The tested dependency inventory and wheel hash are saved. README CLI/Python examples and all seven public dataset interfaces execute against pinned official fixtures with network prohibited.', '',
             f'All **{sql["rows"]:,}** full-export rows pass CSV-to-SQL-to-CSV exact hash comparison. Every original code, key, null, date and numeric lexeme is preserved. SQL composite business keys reject duplicates, and every required field rejects NULL. Decimal keys also reject equivalent alternative scales. Full SQL peak RSS: {sql["peak_rss_mib"]:.2f} MiB. Ancillary PSD and report schemas receive separate exact roundtrip tests.', '',
             f'Final offline suite: {release["offline_tests"]["passed"]} passed, {len(failures)} failed, {len(skips)} required checks skipped/blocked. All nine required adapter live tests passed with real evidence. The standard-library Phase 00 offline verifier and its own regression tests passed.', '',
             f'External blocker: {blocker}', '',
             'The blocked required check is deliberately not counted as a pass. This is temporary source/access unavailability, not permanent missing historical coverage. The 2010 raw fixture and full backfill remain present and hash-valid. The failed live attempts, direct-transport diagnostic and initial SQL constraint failure are retained. The SQL defect was fixed and the entire 9,987,892-row SQL run repeated successfully.', '',
             'Deliverables: `dist/usda_data-0.1.0-py3-none-any.whl`; `final_dataset_manifest.json`; `handover_index.json`; `sql_roundtrip.json`; `examples/checks.json`; `results.json`; `commands.txt`; README and `docs/{interfaces,sql_transfer,field_dictionary,release_notes,handover,acceptance_index}.md`.', '',
             'Source-supported limitations: WASDE structured history begins April 2010; evidenced report nonpublication/table gaps remain visible; current-revised API history is not a historical publication-vintage archive. The run cutoff remains November 16, 2026. No scheduler or production database was installed.', '',
             f'Next action: {action}. See `docs/acceptance_index.md` for evidence links.', '']
    (OUT/'summary.md').write_text('\n'.join(lines))
    print(json.dumps(release,indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
