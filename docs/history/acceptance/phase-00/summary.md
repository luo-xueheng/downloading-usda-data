# Phase 00 acceptance report

Phase: 00 - Scope, source verification, and reference inventory  
Status: **passed**  
Completed (UTC): 2026-11-12T14:48:50.910154+00:00  
Authorized work: Phase 00 only; Phases 01-10 remain `not_started`.  
Scope/configuration SHA-256: `2dc482041973696a23f174c2527622fc8431b8c5639227fb71b5c3181d93c55d`  
Git revision: `726fa52aab88f187fd28d742277b918a26821785`  
Uncommitted source-tree SHA-256: `153641c734d16c2b9d3c4b568e636f5c38fc5855dac4d3af6a53f3b780de8f68`  
Source-tree hash definition: scripts, config, stable docs, fixture catalog and independent references; raw bytes are pinned in catalog; mutable execution ledger/results excluded.

## Deliverables created or updated

- `config/scope.json`: exactly seven datasets, exclusions, date/year defaults, report boundaries and later API inventory-expansion rules.
- `config/expected_coverage.json`: 926 public file/report candidates, including all ERS main-page downloads and explicit unresolved directory gaps.
- `docs/source_registry.md` and `config/source_registry.json`: eight source records, access evidence, authentication, formats, coverage limits and 14 publication records.
- `docs/execution_status.md`, `docs/decisions.md`, `docs/credential_setup.md`: phase ledger, frozen decisions and safe user-supplied API-key instructions.
- `tests/fixtures/catalog.json`: 14 original official files, frozen acquisition hashes and six separately selected development/holdout pairs.
- `tests/fixtures/references/observations.json` and `pages/`: 38 independently read reference values, exact dimensions and units, locators, vintage metadata, pinned PDF page transcripts and visually reviewed PNGs.
- `scripts/verify_phase00.py`: standalone Python standard-library offline/live verifier. `scripts/acquire_phase00.py` accepts explicit URL jobs; `scripts/inventory_phase00.py` inventories saved pages only. These are Phase 00 evidence utilities.
- `scripts/test_verify_phase00.py`: isolated synthetic corruption checks; no official fixture is modified by these tests.
- `README.md`: Phase 00 status, evidence links and runnable verification commands.

## Mandatory acceptance results

| Test ID | Offline | Live mode | Evidence |
|---|---|---|---|
| P00-A1 | pass | pass | `results.offline.json`, `results.live.json`, `results.json` |
| P00-A2 | pass | pass | `results.offline.json`, `results.live.json`, `results.json` |
| P00-A3 | pass | pass | `results.offline.json`, `results.live.json`, `results.json` |
| P00-A4 | pass | pass | `results.offline.json`, `results.live.json`, `results.json` |
| P00-A5 | pass | pass | `results.offline.json`, `results.live.json`, `results.json` |
| P00-A6 | pass | pass | `results.offline.json`, `results.live.json`, `results.json` |

Mandatory IDs passed / failed / blocked: **6 / 0 / 0** in each mode. All six IDs are collected in both modes. Live mode adds six actual discovery requests to P00-A2 and six artifact requests to P00-A4; P00-A1/A3/A5/A6 revalidate the pinned scope, publication evidence, references and credential hygiene. No required live check was skipped.

Twelve unauthenticated live GETs passed. Their response dates, HTTP status, final URL, byte count, SHA-256 and frozen-byte comparison are in `live_checks.json`. Changed landing-page bytes are stored separately under `live_responses/`; frozen fixtures are not overwritten. Live checks use no API key.

Nine verifier self-checks passed: one offline baseline with network access explicitly forbidden and eight deliberate corruptions (missing dataset, omitted inventory item, falsely verified broken discovery, missing publication locator, damaged holdout, wrong expected value, wrong business dimension and synthetic credential assignment). These synthetic cases are never counted as source observations. See `verifier_selftests.json`.

## Commands and exit codes

Working directory: `/Users/tinaluo/Documents/nexus实习/downloading-usda-data`.

| Command | Final exit code |
|---|---:|
| `python3 scripts/verify_phase00.py --mode offline --evidence-dir artifacts/acceptance/phase-00` | 0 |
| `python3 scripts/verify_phase00.py --mode live --evidence-dir artifacts/acceptance/phase-00` | 0 |
| `python3 -B scripts/test_verify_phase00.py` | 0 |
| `python3 scripts/inventory_phase00.py` | 0 |
| `python3 artifacts/acceptance/phase-00/author_references.py` | 0 |

`commands.txt` retains verifier commands, UTC times, interpreter and exit codes. `acquisition_commands.txt` records the seven acquisition batches, rendering commands, initial external-access failures, and the repaired macOS temporary-path alias in the test harness. PDF text reading used bundled pypdf; rendering used pdftoppm. No extra dependency is required to run the verifier. No package installation, production adapter or downstream phase was performed.

## Official artifacts and SHA-256 references

All files below are byte-for-byte source material. URLs, final responses, HTTP Last-Modified (when available), retrieval timestamps and content lengths are preserved in the catalog and adjacent `.acquisition.json` records. A transport timestamp is not asserted to be a source publication timestamp.

| Artifact | Role | SHA-256 |
|---|---|---|
| `tests/fixtures/raw/ers-development.csv` | development | `a42362ce2c9b8f6a5992ae11ef6cb1ed12e25ec59b694782572daea646113951` |
| `tests/fixtures/raw/ers-holdout.csv` | holdout | `c917b5f19620d1b82c289ce6cca5df270b004e5cd35368c13181efe7c55e1b86` |
| `tests/fixtures/raw/grain-trade-development.pdf` | development | `89ad55b237200bf484facb5bf5f52093fceb887c90f05443f65a80e23b8fd0ff` |
| `tests/fixtures/raw/grain-trade-holdout.pdf` | holdout | `a8f68f38aa1bdcc2a65b1efd56fc416407a7f2571233caa56ab970cb6df7211d` |
| `tests/fixtures/raw/oilseed-trade-development.pdf` | development | `9764ad271e29b8b79f4a63afac08cbfb6c9f1797206b480b75a2e5402d808409` |
| `tests/fixtures/raw/oilseed-trade-holdout.pdf` | holdout | `64c77f13ec5f976bab3a3668bab28ea2acfb331e83130e4252b3b3c0b3796998` |
| `tests/fixtures/raw/rma-development.zip` | development | `c66d887d099c437327780238c9679ca1d1fd1350ab1dd42107ecee9382e74a58` |
| `tests/fixtures/raw/rma-holdout.zip` | holdout | `bd503a5248f33305e5d4d671430dada27e4d744c0f88d8f015db0e2e6f7f2185` |
| `tests/fixtures/raw/rma-layout.pdf` | layout | `fd62972c8219e1e6cb90c4b1ae2f7ad3ada3e759c12c007b2b379da55e606307` |
| `tests/fixtures/raw/wasde-development.xml` | development | `c285bbba0e9228dfa91f255cdbdacc7612718162d264fe09fe53050ce016780a` |
| `tests/fixtures/raw/wasde-holdout.xml` | holdout | `85e67ec8e8ec8eb98462596a4e784c170534630108cd51f4f42037756a9e50b9` |
| `tests/fixtures/raw/wasde-supplemental.csv` | supplemental | `1a28972ac0c727ce974e0f8217b3cae9e892f6e974f6927033eaffbd5890a8da` |
| `tests/fixtures/raw/world-production-development.pdf` | development | `6a38ed331521b3f1771951f276306c9d36cb6dd75a6ba7806844929b2555f141` |
| `tests/fixtures/raw/world-production-holdout.pdf` | holdout | `1b1bea88267db8f1c7bfb1f92946ca53ebe48c357109581b27f4a6e7112eb922` |

Total original fixture bytes: **35,827,328**. Holdouts were selected before source adapter implementation. Their first adapter-run results are deliberately left `not_run` until the relevant source phase; Phase 00 verification does not substitute for that test.

## Independent numerical comparisons

**38 of 38** selected source observations agree exactly (Decimal comparison; tolerance zero frozen before verification):

| Source | Observations | Reference selection |
|---|---:|---|
| WASDE | 8 | Six World Total Grains XML cells across two vintages; two Mexico sugar CSV cells |
| ERS | 6 | Three full-dimension records each for corn and soybeans |
| RMA | 6 | Policies, quantity and indemnity from two commodity years, with all grouping dimensions |
| World Agricultural Production | 6 | Production, yield and area on page 1 in each vintage |
| Grain: World Markets and Trade | 6 | Wheat production, three countries, same report's final displayed marketing-year column |
| Oilseeds: World Markets and Trade | 6 | World soybean, rapeseed and cottonseed production, same report's final displayed column |

`source_checks.csv` records every expected/observed value, unit, vintage, dimensions, locator and artifact hash. The expectations were manually authored from official material, independently of any application parser. PDF references were visually checked against rendered pages because generic text extraction merges/reorders some other columns. No PSD-to-report cross-vintage equality or production-adapter accuracy is claimed.

## Coverage and row-count reconciliation

The frozen source inventory reconciles as **926 = 14 downloaded/verified + 912 discovered/not fetched**. Source counts: WASDE 80, ERS 73, RMA 44, and 243 month candidates for each of three FAS families. The global FAS directory lists months, not per-family availability guarantees. Later phases must discover and verify actual partition availability before full-backfill acceptance.

The November WASDE XML additionally exposes 30 report-table nodes in the initial table inventory. Table transformations, normalization row counts, package exports and full backfill are not Phase 00 deliverables; no normalized output is claimed. The 38 reference checks reconcile with all 38 expected observations, and the 12 required development/holdout files each have independent references.

## Known source limitations and external dependencies

- Canonical FAS report/program pages and WASDE history paths returned HTTP 403. Error bodies are retained; official PSD application discovery, real PDF downloads and USDA/FAS distribution evidence permit Phase 00 completion. These endpoints are not listed as successfully verified and no permanent absence is inferred.
- Grain/oilseed distribution URLs redirect to a shared search page with identical content; this is not used as a family-specific listing. The PSD directory, saved official application URL rule and PDF identity establish report discovery.
- October 2025 is missing from the saved WASDE CSV links and FAS global month directory. This remains an investigation item, not proven source unavailability or a scope exclusion.
- API credentials were absent. Authenticated ESR/PSD response checks, dictionary codes, per-series historical boundaries and API field contracts remain explicit Phase 04/05 dependencies. No registration or email verification was attempted.
- Report notes describe a 12:00 PSD update and circular release by 12:15, while public schedule metadata lists 12:00PM for the next event. Preserve both artifact kinds. Exact API availability, the applicable timezone for those clock statements, and actual bulk-RMA-ZIP refresh timing need later verification.
- ERS methods/enterprise types and RMA quantity types remain distinct. Earlier RMA 1948-1988 layout is explicitly inventoried as unsupported; Phase 07 must establish actual supported layouts.
- Mutable APIs cannot supply historical monthly vintages merely by returning historical observation years. Current revised data and report vintages remain separate.

Implementation defects still open for Phase 00: **none**.  
External blockers to the Phase 00 gate: **none after public-source alternatives succeeded**. Canonical access restrictions and deferred authenticated API work remain visible limitations, not hidden passing API tests.

Next eligible phase: **01**, only after separate user authorization. Exact next action then: read the plan, ledger and this report; begin package/contracts/storage/test infrastructure. Stop after this Phase 00 delivery under the current instruction.
