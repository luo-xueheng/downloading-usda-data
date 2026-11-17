# Phase 03 acceptance report

Phase: 03 — ERS Commodity Costs and Returns  
Status: **passed**  
Completed UTC: 2026-11-15T12:03:54.514697+00:00  
Configuration hash: `7cc75dbde49589182d422df8b54bf40b088ca1b894e76d59afaffaf5370fcace`  
Git revision: `726fa52aab88f187fd28d742277b918a26821785`  
Source-tree hash: `a974bb2d6864bd58a348a03ccfc7d1a0cd992e3f07cd023fd3c7fa3c367b83f1`

## Deliverables and acceptance

ERS discovery, CSV/XLSX long-form readers, BIFF/XLS historical wide readers,
archived forecast wide/long readers, exact-value schema, complete-file revision
snapshots, partition iterator, Python API and CLI, source dictionaries/dimensions
in schema, docs/costs_returns.md and real sample CSV/schema/manifest are implemented.
The live product page and all 73 linked attachments were acquired and pinned.
73 layouts are exercised: 72 in layout_coverage.json and the reserved historical
holdout separately. The forecast ZIP contains 14 distinct workbook vintages.

P03-A1 through P03-A7: **7 passed / 0 failed / 0 blocked**.
7 offline test cases plus 1 mandatory live case pass. Live: A1; offline: A2-A7.
The real CLI sample has 257 rows: 189 current-revised Corn observations for 2025
and 68 separately identified archived forecast observations for that year.
A sample-only empty forecast partition bug was fixed and covered by the public
CLI test before closure. No partial export was selected after the failed run.

49 independently frozen cells pass across crop/livestock, hog enterprises,
current/old estimates and current/archived forecasts. Values, units, year labels
and dimensions agree exactly; numerical tolerance is zero. Five additional older
holdout references pass. The pre-existing soybean holdout also passes on its first
ERS adapter run. A real historical milk missing cell stays null; negative returns,
zero and multiple units survive schema-guided CSV round-trip.

All XLS numerical cells outside year headers reconcile to distinct output cell
locators; declared data-cell counts equal rows. Every source link is accounted:
55 selected numeric files and 18 equivalent XLSX presentations whose layouts are
also tested. All observed formats are supported. Distinct survey bases, cash vs
full-ownership costs, annual/forecast labels, forecast vintages, hog enterprises,
tobacco classes and per-acre/per-cwt/per-cow units are retained. Original notes and
lexical labels remain in source_extra/source_item. Unknown layouts and markers fail.

Two independently specified Corn cost groups match their source totals within the
predeclared component-rounding allowance, `(component count + 1)*0.005` dollars per
planted acre. See balance_checks.json and the frozen balance_rules.json.
Earlier observation-year updates replace the complete file snapshot; removed
source rows disappear from latest while earlier snapshots remain reproducible.
Python/CLI outputs and CSV reload match exactly. Prior phase regressions: 28 pass.

## Evidence and limitations

Exact test commands/working directory/exit codes: commands.txt. Source files and
SHA-256 acquisition records: tests/fixtures/phase_03/. Download attempts, connection
failures and successful bounded HTTP-client retries remain in this evidence folder.
Live discovery and real numeric receipt: live/discovery_and_sample.json. Independent
comparisons: source_checks.csv. Holdout first run: holdout_first_run.json. Field/key
contract: schemas/ers_costs_returns.v1.json. Real export: sample/exports/.

Historical source methods are not spliced into a comparable time series. Stored
Excel numerical precision is retained without replacing it with display rounding.
Forecast files are distinct publication vintages, not extra realized observations.
Many Historical products end before 2010 and legitimately yield no rows under the
default year range; their files and all supported historical periods remain in
scope. Blank release timestamps and unspecified estimate statuses are not guessed.
Full configured backfill and final SQL transfer remain later-phase requirements.

Implementation defects open for Phase 03: none.  
External blockers: none; initial transport failures were resolved.  
Next eligible phase: 04 — verify FAS access and freeze ESR dictionaries, independent
development/holdout API responses and complete marketing-year semantics.
