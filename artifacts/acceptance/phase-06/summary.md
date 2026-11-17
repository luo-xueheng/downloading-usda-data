# Phase 06 acceptance report

Phase: 06 — Three FAS report datasets and report reconciliation  
Status: **passed**  
Completed UTC: 2026-11-16T03:01:55.716648+00:00  
Configuration hash: `f909d6b8b93d3eb014f092292b295df85ea656f208dee51a54a67c47b47bc3de`  
Git revision: `726fa52aab88f187fd28d742277b918a26821785`  
Source-tree hash: `adba3fbb891e257808756fab6ebd3b641e718e4f3806d75659e088aab289cb2a`

## Deliverables and mandatory acceptance

Three report-family mappings and complete current-PSD/original-report APIs/CLIs;
public download_reports attachment manifests; six verified PDF archives; focused
report table parsers and schemas; frozen required-table inventory and actual table
coverage; metadata/footnote archives; docs/reports.md and three family dictionaries;
independent manual references and real sample exports for every family.

P06-A1 through P06-A6: **6 passed / 0 failed / 0 blocked**. Six offline cases and
one mandatory live case pass with matching final code/configuration hashes. A1
requires both modes; A2-A6 require offline source/behavior comparisons. All six
October/November 2026 attachments are downloaded and their family, embedded month,
SHA-256 and source article publication metadata verified. Samples with separate
report-date and marketing-year bounds and --with-reports pass for all families:
World Production 7,967 rows; Grain Trade 8,643 rows; Oilseed Trade 9,947 rows.

72 manually transcribed cells (12 per report/family/date), visually checked against
rendered original PDF pages before production parser implementation, match exact
values, periods, classifications and units with zero tolerance. Report date and
original artifact hashes are pinned. Current PSD and report-vintage observations
remain separate; current APIs never fill old report tables under old dates.
Same-vintage unit/geography/commodity/period/value mismatches fail. Demonstrated
October/November production differences are explicitly different vintages.

## Table and cell coverage

The frozen November inventory has 77 required table families/dated changes-table
instances: 18 World Production, 29 Grain, and 30 Oilseed (one oilseed table spans two
pages). All numbered tables, grain appendix tables and explicit narrative-body
trade/outlook changes tables are required. Narrative/chart/maps and administrative
pages are explicitly outside structured table extraction. October additionally
contains another coarse-grain prior-year changes table, which is parsed as a
validated type with its own source period, not silently omitted.

Across six reports, 156 table-page instances account for 46,888 displayed input
cells and 46,852 unique business cells. Source-identical repeated Canada/Brazil
rows in oilseed tables retain occurrence counts and all source locators (36 duplicate
cell occurrences across both months); conflicting duplicates fail. Numerical widths,
mandatory table families, empty required tables and malformed pairings are checked.
A deliberately missing required PDF page and changed numeric row layout both fail.

World Production development/holdout: 7,589 cells each. Grain: 6,753 / 6,774.
Oilseed: 9,081 / 9,102 input cells; 9,063 / 9,084 unique cells. See coverage_summary.json,
config/report_coverage.csv and *-accounting.json for row/cell/metadata details.
No available required table in these tested layouts remains unresolved.

Holdout first-run evidence is preserved honestly: World Production first passed;
Grain first found an extra prior-year changes table and Oilseed first found a
page-continuation boundary difference. Both parser/layout defects were fixed and
all original expected numeric values remained unchanged. The final six-report
acceptance passes; initial failures are not overwritten as first-run successes.

## Evidence and limitations

Exact commands and exit codes: commands.txt. Live receipts: live/report_checks.json.
Independent values: source_checks.csv and tests/fixtures/phase_06/references.json.
Source hashes: Phase 00 catalog plus current acquisition receipts and live raw store.
Coverage/interfaces: coverage_summary.json, interface_checks.json, archive_checks.json.
Source definitions, unit captions and footnotes remain in table metadata. Published
sample manifests identify exact source snapshots, schema and export hashes.
Prior phase regressions: 50 passed. Actual credential scan: zero matches.

Unknown older report layouts must still be implemented/accepted during full archive
reconciliation; these sample layouts are not a completed 2010-present backfill.
Source directory omissions remain unresolved until source-supported evidence exists.
World/foreign/region totals overlap countries; no invalid additive aggregate is
created. Exact API/report vintage alignment is never inferred merely from a month.

Implementation defects open for required Phase 06 sample/layout checks: none.  
External blockers: none.  
Next eligible phase: 07 — RMA State/County/Crop/Coverage Level SOB, including exact
28-field layout, signed monetary values, quantity types and streaming annual output.
