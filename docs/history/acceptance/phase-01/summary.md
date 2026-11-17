# Phase 01 acceptance report

Phase: 01 — Package foundation, schemas, and trustworthy storage  
Status: **passed**  
Scope/configuration hash: `7cc75dbde49589182d422df8b54bf40b088ca1b894e76d59afaffaf5370fcace`  
Code revision: `726fa52aab88f187fd28d742277b918a26821785`  
Source-tree hash: `2b1ec626b880b2212e96e6662a193dbc46237d4d48cbcaa17963649e6713177a`

## Deliverables

Installable Python package, module and console CLI, immutable typed HTTP configuration,
error classes, versioned exact-value CSV/schema contracts, initial provenance schema,
content-addressed artifacts, acquisition receipts, parser/schema/config-aware snapshots,
atomic latest selection, run/partition manifests, finite HTTP retries, format checks,
credential sanitization, offline network guard and acceptance recorder. Existing `.env`
and credential helper are preserved. Operational authorization is recorded separately
from the historical Phase 00 scope freeze in `config/execution.json`.

## Mandatory tests

P01-A1 through P01-A7: **7 passed / 0 failed / 0 blocked**; 19 offline test cases.
No live IDs are required for this phase. This is explicitly not a source accuracy claim.
Exact collected test names, modes and outcomes: `test_cases.offline.json`.
Installation/import/module help succeed. Package versions are in `environment.json`.
Editable installation uses the existing local dependencies via a virtual environment
with system-site-packages and `--no-build-isolation`. Clean isolated installation
remains a Phase 10 requirement.

The CSV checks preserve leading zeros, integer zero, null, date, negative exact
Decimal including scale, quoted multiline text, literal null-token text and empty
strings. Identity checks cover changed bytes, parser, schema and configuration;
corruption and nondeterministic outputs fail. Failure injection preserves the old
CSV and latest manifest. HTTP checks cover finite 429/5xx/timeout retries, capped
Retry-After dates/seconds, successful recovery, immediate 401/403 failures, HTML
rejection, byte limits, and cross-origin redirects. Sentinel credentials are absent
from logs, exceptions and manifests; credentials in request URLs are rejected.
Missing dimensions, duplicate business keys and changed fields fail validation.

## Commands and evidence

Exact commands, working directory and exit codes: `commands.txt`.
Installation output: `installation.txt`; pytest output: `pytest.offline.txt`.
All final commands exited 0. Official artifacts: not applicable to this phase.
Independent numerical source comparisons: not applicable. Synthetic contract fixture
SHA-256: `f0e6e771b199d0666d9c7417dda77957db6e7796bce8651f064a32aa2396bd98`.
Coverage: all seven mandatory IDs executed; no dataset backfill or adapter accuracy
is claimed. Phase 00 reference self-checks were rerun: 9 passed.

Known source limitations: unchanged from Phase 00.  
Implementation defects open: none observed in Phase 01 acceptance.  
External blockers: none.  
Next eligible phase: 02; inspect every WASDE structured layout, acquire early and
marketing-year transition evidence, then implement and verify full table coverage.
