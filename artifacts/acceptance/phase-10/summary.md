# Phase 10 — interface, SQL portability and handover

Phase: 10  
Status: **blocked_external**  
Assessed (UTC): 2026-11-16T22:43:26.555836+00:00

Mandatory IDs: 6/7 passed. P10-A1: pass, P10-A2: pass, P10-A3: pass, P10-A4: pass, P10-A5: pass, P10-A6: blocked, P10-A7: pass.

Source-tree hash: `9bbf96ac104a5544b937a3a6655fb598d5fc8340974f6e533bae2fcef66f594d`. Configuration hash: `a42dbeefc47a177833442c757a2198b38b92e3dd334bfe76d78183b288fad26d`.

The regular wheel installs in an isolated Python 3.13.5 environment with no system-site packages and no editable source import. The tested dependency inventory and wheel hash are saved. README CLI/Python examples and all seven public dataset interfaces execute against pinned official fixtures with network prohibited.

All **9,987,892** full-export rows pass CSV-to-SQL-to-CSV exact hash comparison. Every original code, key, null, date and numeric lexeme is preserved. SQL composite business keys reject duplicates, and every required field rejects NULL. Decimal keys also reject equivalent alternative scales. Full SQL peak RSS: 245.62 MiB. Ancillary PSD and report schemas receive separate exact roundtrip tests.

Final offline suite: 106 passed, 0 failed, 1 required checks skipped/blocked. All nine required adapter live tests passed with real evidence. The standard-library Phase 00 offline verifier and its own regression tests passed.

External blocker: Required Phase 00 RMA 2010 ZIP live recheck returns HTTP 502 through proxy and explicit direct transport; immutable historical bytes still validate offline.

The blocked required check is deliberately not counted as a pass. This is temporary source/access unavailability, not permanent missing historical coverage. The 2010 raw fixture and full backfill remain present and hash-valid. The failed live attempts, direct-transport diagnostic and initial SQL constraint failure are retained. The SQL defect was fixed and the entire 9,987,892-row SQL run repeated successfully.

Deliverables: `dist/usda_data-0.1.0-py3-none-any.whl`; `final_dataset_manifest.json`; `handover_index.json`; `sql_roundtrip.json`; `examples/checks.json`; `results.json`; `commands.txt`; README and `docs/{interfaces,sql_transfer,field_dictionary,release_notes,handover,acceptance_index}.md`.

Source-supported limitations: WASDE structured history begins April 2010; evidenced report nonpublication/table gaps remain visible; current-revised API history is not a historical publication-vintage archive. The run cutoff remains November 16, 2026. No scheduler or production database was installed.

Next action: After source recovery, rerun Phase 00 live/offline at matching source hash, Phase 10 acceptance and full offline suite. See `docs/acceptance_index.md` for evidence links.
