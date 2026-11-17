# Phase 09 — full backfill acceptance

Phase: 09
Status: passed
Completed (UTC): 2026-11-16T17:32:31.146473+00:00
Scope/configuration hash: `a42dbeefc47a177833442c757a2198b38b92e3dd334bfe76d78183b288fad26d`
Source-tree hash: `42fc05c3e0d2a60d7f2a4ffea33912fec39b805853da8b2793a191b2c68b2fd3`

All seven mandatory IDs passed with offline and required live evidence. The frozen 805-task run is complete. Seven aggregate datasets contain 9,987,892 rows. Every aggregate references exact component CSV hashes and normalized snapshot versions. The original raw archives and previous normalized versions remain reproducible.

All 606 listed report attachments were reconciled at the same parser source hash. Explicit nonpublication notices and source-table gaps remain visible. Report peak-memory upper bound was 337.89 MiB against the current 1,024 MiB budget. The post-fix seven-adapter export replay peaked at 689.56 MiB and reproduced exact full-run CSV hashes. The original 512 MiB failure is retained in `full_export_memory.json` and its command receipt; `memory_budget_revision.json` documents the user-authorized increase to 1 GiB and reassessment of the completed measurement. The earlier over-budget threaded trial is retained in the resume logs.

Independent numerical audit: 164 cells across all seven datasets passed, including exact linkage of the 72 report references to full exports. Source accounting covers all selected WASDE/ERS/RMA files and 628 PSD commodity-year partitions. Valid empty ESR responses are preserved as source evidence, without fabricated zero-valued rows. The real ESR unchanged/interruption/resume trial and 37-versus-5,000-row chunk comparison passed.

Coverage: 1417 expected task/report/month records = 1404 succeeded + 13 evidenced source-unavailable; unresolved = 0.

Source limitations: WASDE structured history begins April 2010; January–March 2010 remains explicitly unsupported. The source-confirmed missing report months and June 2016 WAP Table 10 are listed in the coverage/gap evidence. The October 2025 WASDE conclusion uses adjacent official issue numbers and the official funding-lapse note; its inference is explicitly identified in `wasde_gap_evidence.json`. Current-revised API history does not promise historical API publication vintages. Source forecasts/commodity years through 2027 can be present in artifacts already available at the November 16, 2026 cutoff.

Deliverables: `data/exports/datasets/complete.latest.json`, seven versioned CSV/schema outputs, raw/report archives, `coverage_manifest.csv`, `report_coverage.csv`, `report_attachment_inventory.csv`, `report_layout_inventory.json`, `source_accounting.json`, `source_checks.csv`, `final_dataset_manifest.json`, `results.json`, and `commands.txt`.

Commands and exits: see `commands.txt` and command JSON receipts. No implementation defect or external blocker remains in the Phase 09 gate. No scheduler or deployment was installed.

Next eligible phase: 10. Verify clean installation, public interfaces, exact SQL import/readback, all mandatory suites and final handover.
