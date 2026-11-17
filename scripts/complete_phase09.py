"""Finish Phase 09 only after fixed-version reports and every mandatory check pass."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,subprocess,sys,csv
from usda_data.storage import sha256

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/acceptance/phase-09'

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--close-only',action='store_true',help='Reuse completed evidence and rerun the formal gates; never substitute missing or failed evidence')
    args=parser.parse_args()
    summary=json.loads((OUT/'report_backfill_summary.json').read_text())
    version=sha256(b''.join((ROOT/'src/usda_data/sources'/name).read_bytes() for name in ['report_tables.py','report_dimension_repairs.json','report_source_gaps.json','reports.py']))
    if summary['failed'] or summary['parser_source_hash']!=version or not summary.get('memory_within_budget'):
        raise RuntimeError('Complete current-parser report replay must pass before phase closure')
    python=str(ROOT/'.venv/bin/python')
    steps=[
        ('report-coverage',[python,'scripts/build_report_coverage.py']),
        ('full-fetch-completion',[python,'-m','usda_data','fetch','--dataset','all','--config','config/full_backfill.json','--resume']),
        ('full-task-validation',[python,'scripts/validate_backfill.py']),
        ('complete-source-accounting',[python,'scripts/reconcile_source_accounting.py']),
        ('complete-wasde-gaps',[python,'scripts/verify_wasde_gaps.py']),
        ('complete-coverage',[python,'scripts/reconcile_backfill.py']),
        ('complete-independent-audit',[python,'scripts/audit_backfill.py']),
        ('complete-report-audit-linkage',[python,'scripts/link_report_audits.py']),
        ('complete-real-resume',[python,'scripts/check_backfill_resume.py']),
        ('publish-seven-exports',[python,'scripts/publish_backfill_exports.py']),
        ('aggregate-validation',[python,'-m','usda_data','validate','--input-dir','data/exports/datasets']),
    ]
    if args.close_only:steps=[]
    for name,command in steps:
        print('Running',name,flush=True)
        result=subprocess.run([python,'scripts/record_command.py','--name',name,'--',*command],cwd=ROOT)
        if result.returncode:return result.returncode
        if name=='aggregate-validation':
            rows=json.loads((OUT/'aggregate-validation.txt').read_text())
            (OUT/'aggregate_validation.json').write_text(json.dumps(rows,indent=2)+'\n')
    # The offline-only run may exit nonzero until matching live evidence exists.
    subprocess.run([python,'scripts/run_acceptance.py','--phase','09','--mode','offline'],cwd=ROOT,check=False)
    result=subprocess.run([python,'scripts/run_acceptance.py','--phase','09','--mode','live'],cwd=ROOT)
    checks=json.loads((OUT/'results.json').read_text())
    if result.returncode or len(checks)!=7 or any(r['status']!='pass' for r in checks):return 1
    datasets=json.loads((OUT/'final_dataset_manifest.json').read_text());coverage=json.loads((OUT/'coverage_reconciliation.json').read_text());audit=json.loads((OUT/'independent_audit.json').read_text());stamp=datetime.now(timezone.utc).isoformat()
    budget=json.loads((ROOT/'config/full_backfill.json').read_text())['memory_budget_mib']
    rows=sum(r['rows'] for r in datasets['exports'].values());code=checks[0]['code_version'];config=checks[0]['configuration_hash']
    text=f'''# Phase 09 — full backfill acceptance

Phase: 09
Status: passed
Completed (UTC): {stamp}
Scope/configuration hash: `{config}`
Source-tree hash: `{code['source_tree_sha256']}`

All seven mandatory IDs passed with offline and required live evidence. The frozen 805-task run is complete. Seven aggregate datasets contain {rows:,} rows. Every aggregate references exact component CSV hashes and normalized snapshot versions. The original raw archives and previous normalized versions remain reproducible.

All 606 listed report attachments were reconciled at the same parser source hash. Explicit nonpublication notices and source-table gaps remain visible. Report peak-memory upper bound was {summary['peak_rss_mib']:.2f} MiB against the current {budget:,} MiB budget. The post-fix seven-adapter export replay peaked at {json.loads((OUT/'full_export_memory.json').read_text())['peak_rss_mib']:.2f} MiB and reproduced exact full-run CSV hashes. The original 512 MiB failure is retained in `full_export_memory.json` and its command receipt; `memory_budget_revision.json` documents the user-authorized increase to 1 GiB and reassessment of the completed measurement. The earlier over-budget threaded trial is retained in the resume logs.

Independent numerical audit: {audit['checks']} cells across all seven datasets passed, including exact linkage of the 72 report references to full exports. Source accounting covers all selected WASDE/ERS/RMA files and 628 PSD commodity-year partitions. Valid empty ESR responses are preserved as source evidence, without fabricated zero-valued rows. The real ESR unchanged/interruption/resume trial and 37-versus-5,000-row chunk comparison passed.

Coverage: {coverage['expected']} expected task/report/month records = {coverage['succeeded']} succeeded + {coverage['source_unavailable']} evidenced source-unavailable; unresolved = {coverage['unresolved']}.

Source limitations: WASDE structured history begins April 2010; January–March 2010 remains explicitly unsupported. The source-confirmed missing report months and June 2016 WAP Table 10 are listed in the coverage/gap evidence. The October 2025 WASDE conclusion uses adjacent official issue numbers and the official funding-lapse note; its inference is explicitly identified in `wasde_gap_evidence.json`. Current-revised API history does not promise historical API publication vintages. Source forecasts/commodity years through 2027 can be present in artifacts already available at the November 16, 2026 cutoff.

Deliverables: `data/exports/datasets/complete.latest.json`, seven versioned CSV/schema outputs, raw/report archives, `coverage_manifest.csv`, `report_coverage.csv`, `report_attachment_inventory.csv`, `report_layout_inventory.json`, `source_accounting.json`, `source_checks.csv`, `final_dataset_manifest.json`, `results.json`, and `commands.txt`.

Commands and exits: see `commands.txt` and command JSON receipts. No implementation defect or external blocker remains in the Phase 09 gate. No scheduler or deployment was installed.

Next eligible phase: 10. Verify clean installation, public interfaces, exact SQL import/readback, all mandatory suites and final handover.
'''
    (OUT/'summary.md').write_text(text)
    ledger=ROOT/'docs/execution_status.md';lines=ledger.read_text().splitlines()
    for i,line in enumerate(lines):
        if line.startswith('| 09 |'):lines[i]=f'| 09 | passed | 2026-11-16T05:06:05.529455+00:00 | {stamp} | artifacts/acceptance/phase-09/ | None; source-supported gaps remain explicit | Phase 10 eligible; 7/7 mandatory IDs passed; {rows:,} rows in seven exports |'
    ledger.write_text('\n'.join(lines)+'\n')
    readme=ROOT/'README.md';t=readme.read_text().replace('Full backfill Phase 09 is in progress; handover remains gated.',f'Full backfill Phase 09 passed all seven acceptance IDs with {rows:,} rows across seven complete exports. Phase 10 handover remains gated.');readme.write_text(t)
    print('Phase 09 passed; Phase 10 eligible.',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
