# Phase 07 acceptance report

Phase: 07 — RMA Summary of Business with coverage level  
Status: **passed**  
Completed UTC: 2026-11-16T03:41:58.499028+00:00  
Configuration hash: `1cc506213f5b1ad6226e06db26468bbc99def462853e82103075e549c5999e4a`  
Git revision: `726fa52aab88f187fd28d742277b918a26821785`  
Source-tree hash: `0784ae10a6c2252e5a25ffeebe12227c2638fe5bce84a4d5bb2834a40b7854ab`

## Deliverables and mandatory results

RMA discovery/layout verification, safe ZIP-member and strict 28-field readers,
complete grouping-key schema, quantity-type dictionary, source-year layout map,
chunk iterator, disk-backed global key checks and atomic annual publication,
public download_rma_sob, CLI commodity-year/all-history options, docs/rma_sob.md,
real annual sample export and exact source comparison/coverage evidence.

P07-A1 through P07-A7: **7 passed / 0 failed / 0 blocked**.
Six offline cases and one mandatory live case pass. Live: A1; offline: A2-A7.
135 independently read field values across two years, multiple state/county areas
and coverage/plan categories match exactly. Full source rows reconcile: 2025 has
155,676 and the reserved 2010 holdout has 128,165. The older holdout passed its first
adapter run without changing any frozen expectations. Global complete-key uniqueness
passes; no source rows are silently removed.

Four independently calculated disjoint leaf-county source-row subtotals match exact
integer money and quantities; missing-component exclusions are explicit and counted.
Actual non-acre types include Pounds, Tons, Trees, Colonies, Vines and shellfish/clam
counts. Leading-zero state/county/crop/plan codes and all grouping dimensions survive.
The real signed indemnity adjustment and negative loss ratio are retained. Actual
blank fields stay null: the 2025 fixture has 448 missing net quantities and one
missing liability, premium and loss-ratio value. No missing value becomes zero.

Malformed field widths/ZIP layouts and unsupported pre-1989 requests fail. A failed
stream publication preserves its prior selected annual snapshot. Cross-chunk duplicate
keys fail even when equivalent Decimal coverage levels have different lexical scales.
Chunk sizes 5,000 and 997 produce exactly the same complete annual snapshot/hash.
Python and CLI observations plus schema-guided CSV reload match exactly.

## Resource behavior and source evidence

The real CLI annual sample has 155,676 rows and one selected snapshot. Peak resident
memory measured by /usr/bin/time is 285,769,728 bytes, below a documented 512 MiB
budget for this bounded annual CLI path. Raw ZIP text is read by chunks, full key
uniqueness uses a temporary SQLite table, and large normalized hashes/CSV reads
stream from disk. The public DataFrame convenience function deliberately materializes
its requested result; the CLI/iterator is the bounded-memory interface.

Live discovery fetched a real ZIP and current applicable layout and validated all
member records. Exact receipts and accounting: live/checks.json. Source fixture
hashes, inventories and independent references: tests/fixtures/phase_07/. Numerical
checks: source_checks.csv; subtotals: subtotal_checks.json; first holdout run:
holdout_first_run.json; quantity types: quantity_types.json. Real CSV, sidecar schema
and snapshot/hash manifest: sample/exports/. Exact commands and exits: commands.txt.
Prior phase regression suite: 56 passed.

Known source limitations: 1948-1988 is a separate unsupported layout, explicitly
reported by all-history. Quantity types cannot be added together; policy counts and
endorsement/base coverage can overlap. Arithmetic source-row subtotals are not
unique-farm or unique-policy estimates. Exact publication time is not inferred from
HTTP Last-Modified. Source year labels can include future commodity years already
published. Full all-history/backfill acceptance remains Phase 09.

Implementation defects open for mandatory Phase 07: none.  
External blockers: none.  
Next eligible phase: 08 — integrate revision refresh policies, publication calendars,
resumable partial jobs and atomic complete-run export selection across all sources.
