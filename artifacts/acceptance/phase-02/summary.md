# Phase 02 acceptance report

Phase: 02 — WASDE historical and current-release data  
Status: **passed**  
Completed UTC: 2026-11-15T11:02:46.873264+00:00  
Configuration hash: `7cc75dbde49589182d422df8b54bf40b088ca1b894e76d59afaffaf5370fcace`  
Git revision: `726fa52aab88f187fd28d742277b918a26821785`  
Source-tree hash: `1b466d5e17281727ced749ffadf0e3743ce2fc3a79d4637d59ad46e97ef7033d`

## Deliverables and verified behavior

WASDE adapter, exact-decimal version 2 schema, public `download_wasde`,
`download_dataset`, and partition iterator; matching CLI fetch with atomic complete
CSV export; `docs/wasde.md`; independently pinned early/transition/current/holdout
fixtures; source receipt/hash archives; complete current table-family inventory;
current XML footnotes and zero-tolerance summary reconciliation. `sample/exports/`
contains the real CLI output (5,054 rows), machine-readable schema and manifest.

## Mandatory test results

P02-A1 through P02-A7: **7 passed / 0 failed / 0 blocked**.
9 offline test cases and 1 mandatory live case passed. Offline IDs: A2-A7;
live ID: A1. Exact commands/exit codes and node-level outcomes are in commands.txt,
results.json and test_cases.*.json. Initial network failures were not counted as
passes; the final bounded real check succeeded after official fallback support.
Phase 01 regression run on the updated common HTTP/dependency code: 19 passed.

36 independent values span April 2010, May 2026 marketing-year transition and
November 2026, including livestock, dairy and reliability statistics. Expectations
were frozen before adapter implementation. All values, dimensions, periods and
units match at source precision. 360 current XML/CSV observations agree exactly;
an injected conflict rejects publication and leaves the prior selected version.
The separately selected October holdout passed its first adapter run, including
12 independent references and summary reconciliation; see holdout_first_run.json.

## Coverage, sources and limitations

November 2026: 5,054 observations across all 28 CSV table families. May 2026: 4,988
observations. April 2010: 4,758 observations. Complete parser cell counts and
out-of-range exclusions are in table_coverage.json. Empty observations retain
missing status and remain distinct from zero. Keys preserve every original source
classification and vintage. Current, early and transition fixture hashes/URLs are
in tests/fixtures/phase_02/catalog.json; older public fixture hashes remain in the
Phase 00 catalog. Live receipts and the current hash/date are in live/.

The original 2010-2015 source has seven omitted Pork Production labels and three
omitted quantity units in May 2011. These are repaired only for the exact pinned
artifact and exact original records using independently inspected official PDF
page 37; original fields and evidence IDs remain in output. A 3.50 CSV versus 3.4
PDF RMSE disagreement is exposed as `source_conflict`; CSV numeric values are
retained according to the explicit source precedence policy, not merged with PDF
numbers or falsely declared equal. Full evidence is in source_dimension_repairs.json.
The numeric source scope and tolerances have not changed.

Historical structured files begin April 2010; no January 2010 coverage is invented.
Historical time-only fields are preserved with date-level confirmed UTC precision.
XML previous-month display columns remain archived and are explicitly excluded from
the current forecast comparison; CSV is the complete chosen numeric format.
Source access failures use a verified official distribution copy where available,
with both original failure and successful URL recorded. Historical full backfill
and source-wide reconciliation remain Phase 09 work; sample success is not a
full-history success claim.

Implementation defects still open for mandatory Phase 02 checks: none.  
External blockers: none.  
Next eligible phase: 03 — inventory all ERS variants and layouts, pin independent
crop/livestock/recent/historical/forecast references before implementing readers.
