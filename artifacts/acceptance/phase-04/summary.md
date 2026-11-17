# Phase 04 acceptance report

Phase: 04 — FAS Export Sales Reporting  
Status: **passed**  
Completed UTC: 2026-11-15T13:19:09.529347+00:00  
Configuration hash: `c4aa07b51dc3167f2c3a76b34d99b6611ccf8c13096f9468d9a4411fe0910763`  
Git revision: `726fa52aab88f187fd28d742277b918a26821785`  
Source-tree hash: `2d2163aab25b40dfd67cc01ed0c54f9d39d4bc9c91f7504a6a07294560a4fa99`

## Deliverables

Authenticated ESR dictionary and full commodity/year downloads; exact schema,
source code/name selection, eight separately retained metrics, public API and CLI,
complete-partition refresh, revision archives, secure environment/.env loading,
explicit FAS transport configuration, docs/export_sales.md, seven pinned numeric
partitions (including one preselected holdout), independent references, and a real
7,714-row CLI CSV with schema and content/partition manifests.

## Acceptance results

P04-A1 through P04-A7: **7 passed / 0 failed / 0 blocked**.
7 offline test cases and 1 live test case passed. Live: A1; offline: A2-A7.
66 independently frozen metric values cover three commodities, two destinations,
two source marketing years and real negative net sales. Values, dimensions, units
and year labels match exactly. The preselected Sorghum 2026 holdout passed its
first adapter run: 553 records, 11 independently read values, public/CLI equality
and lossless CSV reload.

All six development response record counts reconcile exactly. Unknown codes,
changed layouts, malformed/truncated JSON and independently counted incomplete
responses fail. Two separate destination endpoint responses, each 53 records,
match all-country subsets exactly; a fresh authenticated live comparison passes.
The source exposes complete arrays, no documented pagination/count envelope.
This validates the transformation and endpoint behavior, not an unprovable claim
that the upstream service can never omit a record.

The June 5, 2025 wheat boundary week remains in both source 2025 and 2026 marketing
years. Publication dates are not inferred from weekly dates or unzoned latest
commodity-release metadata. Synthetic and real cancellations retain negative
values. A simulated older-year update removes a source row and changes a value;
the whole requested older partition refreshes, its predecessor remains readable,
and the unchanged newer partition reuses its snapshot. Missing credentials fail
before any network/output; a call-time working-directory .env regression was fixed.

## Sources, access and scope

Real authenticated dictionaries contain 44 commodities, 211 destinations, 12
regions and 5 units; config/esr_inventory.json freezes their exact fields, hashes
and scope. All source commodities remain required, including nondevelopment
products. Marketing years retain the endpoint identifier; full per-commodity
historical availability is established at Phase 09's backfill cutoff.

Initial proxy and standalone urllib checks could not connect. Bounded diagnostics
showed proxy ConnectError with and without a key; direct authenticated TLS returned
HTTP 200 JSON. The explicit fas_http.trust_environment=false setting resolves this
workstation issue without changing other source transports or logging credentials.
Original failures, direct-success diagnostics and acquisition receipts are retained.

Commands/exit codes: commands.txt. Exact field/row/live receipts:
live/authenticated_checks.json. Numeric/source comparisons: source_checks.csv.
Pinned numeric and dictionary hashes: tests/fixtures/phase_04/*.acquisition.json
and catalog.json. Holdout first run: holdout_first_run.json. Independent destination
checks: completeness_checks.json. Prior phase regressions: 35 passed.

Known source limits: current-revised historical observations, not unavailable
original weekly publication vintages; source units/aggregates remain distinct.
An empty API array is explicitly recorded and cannot alone prove permanent
unavailability or historical first coverage. No full backfill is claimed here.
Implementation defects open for mandatory Phase 04 checks: none.  
External blockers: none.  
Next eligible phase: 05 — verify PSD dictionaries and source schemas, freeze only
the commodity/attribute union required by the three requested report families.
