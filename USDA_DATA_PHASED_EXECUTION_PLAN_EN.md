**USDA Data Collection: Phased Execution Plan for Codex**

> Repository cleanup (2026-11-17): historical `artifacts/` and full `data/` paths below refer to the external archive. See [migration and archive guide](docs/repository_cleanup.md). These saved results are not current test results.


Document version: 1.0  
Prepared: 2026-11-12, Asia/Shanghai  
Status: Execution specification with recorded implementation progress; see docs/execution_status.md and per-phase acceptance evidence.  
Companion document: `USDA_DATA_IMPLEMENTATION_PLAN.md`  
Purpose: Give an implementing agent concrete tasks, deliverables, accuracy checks, dependencies, and completion gates.

**1. Execution mandate**

Build a modular Python package that downloads the seven datasets below, exposes public functions returning pandas DataFrames, and provides a CLI producing SQL-ready CSV files and schema metadata. Preserve source evidence, publication timing, and revisions.

This document reorganizes the existing implementation plan. Source descriptions and release rules inherited from that plan are starting hypotheses for verification, not proof of current endpoint behavior. Verify official documentation and real responses during implementation. Do not mark any phase complete on the strength of this document alone.

When instructed to implement this plan:

1. Read repository instructions and inspect existing code, data, and working-tree changes before editing.
2. Start with Phase 00, or resume the first incomplete phase whose dependencies are satisfied.
3. Implement each phase's deliverables, execute its tests, and save the evidence specified below.
4. Fix failed tests without weakening expectations to match an incorrect implementation.
5. Advance to a dependent phase only after its prerequisites pass. Continue independent phases when one source is externally blocked.
6. Update the execution ledger after each meaningful milestone. Report completed work, failures, external blockers, and the next actionable step.
7. Do not overwrite unrelated work, commit credentials, register a fictional account, or substitute synthetic data for a real download.
8. Do not deploy services, create recurring jobs, send messages, or publish a repository as part of this plan. Those are separate actions.

All instructions, code comments, field dictionaries, acceptance reports, and user documentation produced under this plan should be in English.

**2. Fixed scope and defaults**

| Dataset ID | Required business output | Shared implementation |
|---|---|---|
| `wasde` | Report-vintage supply and demand observations | WASDE file adapter |
| `export-sales` | Weekly export sales, shipments, and outstanding commitments | FAS ESR adapter |
| `world-production` | Production-related country/commodity/year observations and report archive | FAS PSD adapter plus report mappings |
| `grain-trade` | Grain supply, demand, and trade observations and report archive | FAS PSD adapter plus report mappings |
| `oilseed-trade` | Oilseed, meal, and oil observations and report archive | FAS PSD adapter plus report mappings |
| `costs-returns` | Commodity production cost and return observations | ERS file adapter |
| `rma-sob` | State/county/crop/coverage-level insurance business observations | RMA SOB file adapter |

Defaults to apply unless the user changes them:

- Backfill from 2010 through the latest available source data at run time. Discover the actual first available period for every series; do not invent January 2010 coverage.
- WASDE dates refer to report publication dates. ESR/PSD use marketing-year identifiers. ERS uses observation years. RMA uses commodity years. Preserve each source's original year labeling and meaning.
- Cover all commodities, regions, and indicators included in the frozen dataset inventory. Corn, soybeans, and wheat are development samples, not the final scope.
- Scope PSD to the three requested report families. Do not expand automatically to unrelated PSD report families.
- Include ERS Recent, Historical, and forecast files on the main product page. Keep their methods and enterprise types distinct. Separately linked Organic products are outside this release.
- Use RMA State/County/Crop/Coverage Level SOB files. Cause of Loss, FSA prevented planting, and more detailed RMA products are outside this release.
- Do not reimplement NASS Crop Progress & Condition or Crop Production.
- Preserve downloaded raw artifacts and subsequent revisions. Historical monthly vintages unavailable from a current API are not promised by this release.
- Archive available FAS reports within the configured report-date interval. Any gaps must have evidence and remain visible in the coverage manifest.
- `--all-history` means all available history supported by an implemented layout. It must explicitly report earlier unsupported layouts; it cannot silently imply they were downloaded.
- Provide scheduling instructions and an executable `sync` command; do not install an actual scheduler.

Freeze scope in `test/fixtures/config/scope.json` during Phase 00. Later changes require an entry in `docs/decisions.md`, an updated expected-coverage inventory, and appropriate regression checks. Do not silently narrow scope to make tests pass.

**3. Phase map and execution order**

| Phase | Objective | Required predecessors | Evidence directory |
|---|---|---|---|
| 00 | Confirm scope, sources, and independent reference evidence | None | `artifacts/acceptance/phase-00/` |
| 01 | Build package, contracts, storage, and test infrastructure | 00 | `artifacts/acceptance/phase-01/` |
| 02 | Deliver WASDE end to end | 01 | `artifacts/acceptance/phase-02/` |
| 03 | Deliver ERS costs and returns end to end | 01 | `artifacts/acceptance/phase-03/` |
| 04 | Deliver FAS export sales end to end | 01 plus valid API access | `artifacts/acceptance/phase-04/` |
| 05 | Deliver shared PSD observations | 01 plus valid API access | `artifacts/acceptance/phase-05/` |
| 06 | Deliver all three FAS report datasets | 05 | `artifacts/acceptance/phase-06/` |
| 07 | Deliver RMA SOB end to end | 01 | `artifacts/acceptance/phase-07/` |
| 08 | Integrate updates, publication calendars, and recovery | 02, 03, 04, 06, 07 | `artifacts/acceptance/phase-08/` |
| 09 | Run complete configured backfill and reconcile coverage | 08 | `artifacts/acceptance/phase-09/` |
| 10 | Validate clean installation, SQL transfer, and handover | 09 | `artifacts/acceptance/phase-10/` |

Default order is numerical. If API access is unavailable, complete Phases 02, 03, and 07 and the independently testable portions of Phase 08. Leave dependent phases blocked. This dependency structure does not itself authorize launching subagents.

**4. Common acceptance rules**

**4.1 Status and evidence**

Create `docs/execution_status.md` with one row per phase: status, start time, completion time, evidence path, blocker, and next action. Allowed statuses are `not_started`, `in_progress`, `blocked_external`, `failed`, and `passed`.

Every phase must produce these files inside its evidence directory:

```text
summary.md              What was implemented, verified, and left unresolved
results.json            One result per acceptance-test ID
commands.txt            Exact commands, working directory, and exit codes
source_checks.csv       Reference comparisons, or an explicit not-applicable record
```

`results.json` must include phase ID, test ID, status (`pass`, `fail`, or `blocked`), observed result, expected result, evidence path, code version, configuration hash, and UTC execution time. Use a Git revision when available and a source-tree hash when work is uncommitted. Never record credentials or unredacted authentication headers.

A phase passes only when all mandatory test IDs pass, its required live checks run, and its required deliverables exist. A skipped live test is blocked, not passed. Documentation of a defect does not turn the defect into a passing result.

Independent source unavailability may be recorded as an evidenced coverage limitation. This is distinct from an implementation failure. An inaccessible source caused by a temporary outage cannot be declared permanently unavailable to satisfy a gate.

**4.2 Reference data must be independent**

For each source, save small official raw fixtures and manually or independently read expected observations. Record source URL, artifact SHA-256, release/as-of information, worksheet/table/page or JSON field locator, business dimensions, expected value, expected unit, and reference creation method.

- Do not generate expected values by invoking the parser being tested.
- Deterministic fixtures must be pinned by hash and readable without a network connection.
- Synthetic edge cases must be explicitly labeled. They test behavior and cannot satisfy official-source accuracy or live-access requirements.
- Reference comparisons must align publication vintage, commodity, geography, period, indicator, and unit.
- Current revised PSD data must not be expected to equal an older report vintage. Record such differences separately; validate the current API transformation against its own saved response and the report extraction against its own report.
- Keep development fixtures and at least one additional holdout artifact separate for every source adapter. Select the holdout before finalizing that adapter and report its first-run results.
- Freeze the reference artifact and file hash at acquisition so a later source update cannot silently change a test expectation.

**4.3 Numerical and structural thresholds**

| Check | Mandatory acceptance rule |
|---|---|
| Codes, dates, periods, units, and categories | Exact equality after documented normalization |
| Integer counts | Exact equality |
| Decimal source values | Equality at source precision, preferably using Decimal or scaled integers |
| Report display rounding | A declared per-indicator tolerance, at most half the last displayed unit, only when display rounding is demonstrated |
| Derived balance checks | Explicit formula, aligned dimensions, and a tolerance justified from component rounding; not a universal percentage threshold |
| Missing values | Preserve zero versus missing, suppressed, unavailable, and not applicable |
| Business keys | Zero unexplained duplicates within a partition/version |
| Required dimensions and provenance | Zero unexplained nulls |
| Parser accounting | Every input data record/cell is mapped, explicitly excluded with a reason, or quarantined as a failure |
| Frozen required coverage | Every expected partition succeeds or has source-supported unavailability evidence |

Set and record tolerances before looking at comparison failures. Do not increase tolerances to make a mismatch disappear. Source totals and aggregate identities are tested only where the official definitions make them valid.

**4.4 Commands and test organization**

Commands below are target interfaces to implement, not a claim that they already work. Replace angle-bracket placeholders with verified values before execution and save the fully expanded command. Phase 00 uses a standalone standard-library verifier because the package and test environment do not exist yet. Phase 01 adds `pytest` as a development dependency and registers the `live` marker. Offline tests must never send network requests. Live tests must be read-only and must not mutate authoritative production outputs.

Use the phase-specific directories specified below. Common invocation pattern:

```bash
python -m pytest test/phase_XX -m 'not live' -q
python -m pytest test/phase_XX -m live -q
```

Live test IDs and offline test IDs must be listed separately in the phase evidence. An entire phase cannot pass by collecting zero tests. Use small live samples first; the full backfill is performed in Phase 09.

**5. Shared architecture and data contracts**

Create the package in the current repository root, adapting to existing code where appropriate:

```text
pyproject.toml
test/fixtures/config/scope.json
config/datasets.toml
docs/history/config/commodities.toml
docs/history/config/report_mappings.toml
src/usda_data/__init__.py
src/usda_data/__main__.py
src/usda_data/api.py
src/usda_data/cli.py
src/usda_data/http.py
src/usda_data/storage.py
src/usda_data/state.py
src/usda_data/calendar.py
src/usda_data/validation.py
src/usda_data/sources/{wasde,fas_esr,fas_psd,ers_costs_returns,rma_sob,reports}.py
schemas/
docs/
scripts/verify_phase00.py
test/phase_01/ ... test/phase_10/
test/fixtures/
artifacts/acceptance/
data/{raw,normalized,exports,reports,manifests}/
```

Each source adapter implements discovery, fetch, parse, normalize, and validate responsibilities. Shared code handles HTTP behavior, secrets, raw artifact storage, state, and output. CLI code calls the same public functions as Python users.

Required public functions:

```text
download_wasde(start, end, *, data_dir, refresh=False) -> DataFrame
download_export_sales(commodities, market_years, *, countries="all", data_dir, refresh=False) -> DataFrame
download_psd(commodities, market_years, *, countries="all", data_dir, refresh=False) -> DataFrame
download_costs_returns(years, *, commodities="all", data_dir, refresh=False) -> DataFrame
download_rma_sob(commodity_years, *, data_dir, refresh=False) -> DataFrame
download_dataset(dataset, *, data_dir, **validated_dataset_options) -> DataFrame
download_reports(report_family, start, end, *, data_dir, refresh=False) -> DataFrame
```

Use `data_dir="data"` as the default. Public docstrings must explain cache and raw-archive side effects. Reject unsupported options. Large jobs must also have a partition iterator or streaming implementation; do not concatenate all history merely to satisfy the CLI. `download_reports` returns the report manifest and saves attachments; structured report observations are returned through the dataset functions.

Required business tables:

| Table | Grain and key requirements |
|---|---|
| `wasde_observations` | Report vintage, table, commodity, geography, source period, indicator, every actual classification dimension, and unit |
| `esr_weekly_sales` | Commodity, destination, marketing year, week ending, unit, plus any additional official grouping dimensions |
| `psd_observations` | Commodity, geography and aggregation level, marketing year, attribute, and unit |
| `ers_costs_returns` | Commodity, enterprise type, region, year, series family, methodology, item, and unit |
| `rma_sob` | Every official grouping dimension, including commodity year, geography, crop, insurance plan, coverage categories, delivery type, coverage level, and quantity type where present |

Final keys are established from real samples and official definitions. Preserve source dimension labels when normalization is uncertain. A row number or opaque hash is not a substitute for understanding the grain. A hash key may supplement, but never replace, the underlying dimensions.

Every table needs a versioned schema declaring field type, nullability, meaning, source mapping, units, key membership, and missing-value rules. Add raw-value representations where source lexical precision or suppression markers matter.

Provenance fields must distinguish `source_release_date`, nullable `source_release_at_utc`, `release_time_precision`, `retrieved_at_utc`, `source_artifact_id`, `snapshot_id`, and `vintage_type`. Use source-specific codes as strings. Do not infer precise publication timestamps from retrieval time.

Raw bytes identify an artifact; the parser/schema version and configuration also identify a normalized snapshot. Reprocessing identical bytes with a changed parser must not overwrite earlier normalized results.

**Phase 00 — Scope, source verification, and reference inventory**

**Entry requirements:** Repository access. No API key is required to complete public-source discovery.

**Implementation tasks:**

1. Inspect existing repository instructions and changes; identify reusable code and preserve unrelated files.
2. Create the execution ledger, decision log, frozen scope configuration, and source registry.
3. Verify the official landing pages in Appendix A. Discover current download/documentation links rather than trusting old CDN or report URLs.
4. Record each source's authentication, format, coverage limits, publication rule, timezone, precision, and reference evidence. Label unverified claims explicitly.
5. Inventory public WASDE, ERS, and RMA files and FAS report families. Record how API dictionaries will expand the inventory in Phases 04 and 05.
6. Select initial and holdout public artifacts, preserve hashes, and create independently read reference observations. API fixtures are acquired in their respective source phases.
7. Document how the user supplies an API key through `USDA_FAS_API_KEY`. If registration is needed, use the user's real Nexus email only when supplied and authorized; leave email verification to its owner.

**Concrete deliverables:** `test/fixtures/config/scope.json`; `docs/source_registry.md`; `docs/execution_status.md`; `docs/decisions.md`; `docs/credential_setup.md`; `test/fixtures/catalog.json`; independently authored reference files; `scripts/verify_phase00.py` using only the Python standard library.

**Accuracy and acceptance tests:**

| ID | Test and exact expected outcome |
|---|---|
| P00-A1 | Scope lists exactly the seven dataset IDs, exclusions, default date/year rules, and report-family boundaries; none is silently omitted. |
| P00-A2 | Every source has an official landing page, discovery method, access check date, and raw evidence or an explicitly recorded external blocker. Broken links are not listed as verified endpoints. |
| P00-A3 | Each publication claim has an official locator and precision, or is labeled unverified. Report, API, and historical-file timing are separate records. |
| P00-A4 | At least one real artifact from each public numeric source and one report from each FAS report family has a matching SHA-256; fixtures are raw source material, not generated output. |
| P00-A5 | Every reference observation has a locator, exact dimensions, unit, vintage information where available, and independently read expected value. |
| P00-A6 | No secret is in the source registry, fixtures, or logs; absent API access is recorded without preventing public-source work. |

**Commands:** `python scripts/verify_phase00.py --mode offline --evidence-dir artifacts/acceptance/phase-00` and `python scripts/verify_phase00.py --mode live --evidence-dir artifacts/acceptance/phase-00`. Implement lightweight inventory/hash/evidence checks here; do not build a general crawler. Use available browsing/download tools to gather official artifacts, recording their acquisition evidence separately when needed.

**Exit gate:** All six checks pass. Deferred API-response verification is an explicit dependency of Phases 04/05, not a Phase 00 success claim.

**Phase 01 — Package foundation, schemas, and trustworthy storage**

**Entry requirements:** Phase 00 passed.

**Implementation tasks:**

1. Create an installable package, development dependencies, CLI entry point, and test markers.
2. Define error classes, typed configuration, schema metadata, and artifact/run/partition manifests.
3. Implement one HTTP client with timeout, bounded retries, 429 handling, authentication redaction, and response-format checks.
4. Implement content-addressed raw storage, temporary-file writes, atomic publication, and parser-version-aware snapshots.
5. Implement CSV read/write helpers using explicit schemas, nullable values, and leading-zero-safe code columns.
6. Establish offline test fixtures, mock transport, independently stored expected values, and acceptance-result recording.

**Concrete deliverables:** Working `pyproject.toml`; shared modules; `.env.example` without a key; `.gitignore`; initial schema contracts; `test/phase_01/`; install/import/help commands.

**Accuracy and acceptance tests:**

| ID | Test and exact expected outcome |
|---|---|
| P01-A1 | Editable installation, package import, and `python -m usda_data --help` succeed in the declared environment; version and dependency information are recorded. |
| P01-A2 | A fixture containing a leading-zero code, integer zero, null, date, negative decimal, and a quoted text field survives schema-guided CSV round-trip exactly. |
| P01-A3 | Identical bytes retain the same artifact hash; changing one byte changes it. A changed parser/schema version creates a distinct normalized snapshot identity. |
| P01-A4 | Simulated failure before publication leaves the previous file and published manifest unchanged; incomplete temporary output is never selected as latest. |
| P01-A5 | 429 and transient 5xx retry within the configured limit; 401/403 fail explicitly; HTML masquerading as CSV/JSON is rejected. |
| P01-A6 | A sentinel API key never appears in captured logs, exceptions, manifests, or retry diagnostics. |
| P01-A7 | Missing required dimensions and duplicate business keys fail validation; an unauthorized field-layout change cannot silently pass. |

**Commands:** `python -m pip install -e '.[dev]'`, then the Phase 01 offline suite and `python -m usda_data --help`.

**Exit gate:** All seven checks pass. No source-specific business logic is required yet.

**Phase 02 — WASDE historical and current-release data**

**Entry requirements:** Phase 01 passed; public WASDE fixtures available.

**Implementation tasks:**

1. Discover and archive the historical CSV and the currently supported structured release format.
2. Parse historical observations while preserving report vintage, table identity, period, all classifications, units, and footnotes.
3. Implement one verified current-release structured parser; retain an additional format only if needed for coverage or reconciliation.
4. Establish precedence for historical CSV versus current-release data: keep both source artifacts, compare overlapping observations, and record conflicts before selecting a published output.
5. Expose `download_wasde`, CLI fetch, schema, and documented economic meanings.
6. Inventory every required structured table, including non-crop tables. Add special handling for layouts actually encountered.

**Concrete deliverables:** WASDE adapter and schema; `docs/wasde.md`; sample CSV; table-coverage inventory; pinned early/recent/year-transition fixtures; `test/phase_02/`.

**Accuracy and acceptance tests:**

| ID | Test and exact expected outcome |
|---|---|
| P02-A1 | Live discovery fetches and validates a real current artifact; the artifact hash and report date agree with its saved manifest. |
| P02-A2 | At least 30 independently read observations across an early report, a recent report, and a marketing-year transition match values, dimensions, and units exactly at source precision. Include multiple tables and a non-crop table when in scope. |
| P02-A3 | Historical/current-format overlap for the same report is reconciled for at least 10 observations. Any true source conflict remains separately preserved and blocks an unexplained merged result. |
| P02-A4 | The same commodity/year/indicator from two report dates remains two observations; neither is overwritten as a duplicate. |
| P02-A5 | Fixture row/cell accounting balances, all required table families are mapped, and missing/suppressed values are not converted to zero. |
| P02-A6 | Boundary-date filters are inclusive and operate on report dates; public-function and CLI outputs match after canonical sorting. |
| P02-A7 | An additional holdout release passes without changed expected values; its schema/layout is explicitly identified. |

**Commands:** Phase 02 offline/live suites, plus a small `python -m usda_data fetch --dataset wasde --start <verified-start> --end <verified-end> --output-dir <temporary-output>` run. Replace placeholders with the selected fixture interval and record the exact command.

**Exit gate:** All seven checks pass; every required structured table in the tested layouts is either parsed or reported as a blocking coverage defect. Merely archiving a PDF does not satisfy a structured-data requirement.

**Phase 03 — ERS Commodity Costs and Returns**

**Entry requirements:** Phase 01 passed; public ERS fixtures available.

**Implementation tasks:**

1. Discover all in-scope product files, update dates, series families, commodities, and enterprise variants.
2. Implement CSV/XLSX readers and reshape wide year columns into a stable long-form schema where needed.
3. Preserve region, enterprise, methodology, item, unit, observation year, series family, and estimate status.
4. Separate Recent, Historical, and forecast observations even when commodity/year labels overlap.
5. Implement complete-file replacement on revision, public function, CLI, and economic definitions.

**Concrete deliverables:** ERS adapter and schema; `docs/costs_returns.md`; discovery manifest; sample CSVs spanning available series/layouts; `test/phase_03/`.

**Accuracy and acceptance tests:**

| ID | Test and exact expected outcome |
|---|---|
| P03-A1 | Live product discovery accounts for every in-scope download link and variant, with an explicit inclusion/exclusion reason. |
| P03-A2 | At least 30 independent values span available crop/livestock, recent/historical/forecast, and enterprise variants; values, units, and year labels match the source. |
| P03-A3 | Wide-to-long accounting equals the expected source data cells, excluding only documented headers/footnotes; no year or unit becomes a numeric observation accidentally. |
| P03-A4 | Overlapping years in different series/methodologies remain distinguishable. A missing estimate-status label stays unknown rather than being inferred from today's date. |
| P03-A5 | For at least two source-defined additive cost groups, component sums equal the published total within a predeclared rounding tolerance. If no valid group exists, document the source definitions and replace this check with an independently verified transformation test before execution. |
| P03-A6 | An older-file holdout preserves negative returns, zero values, missing cells, and distinct units; no unsupported cross-method splice is created. |
| P03-A7 | Python/CLI output and schema-guided CSV round-trip are equal for the same fixture-backed request. |

**Commands:** Phase 03 offline/live suites; a small `fetch --dataset costs-returns --years <verified-year-range>` run through `python -m usda_data`.

**Exit gate:** All seven checks pass, and all observed in-scope layouts have mappings. A parser that handles only one commodity's file is incomplete.

**Phase 04 — FAS Export Sales Reporting**

**Entry requirements:** Phase 01 passed; valid API access for mandatory live checks.

**Implementation tasks:**

1. Verify current API authentication and schema, then download commodity, destination, unit, and release metadata.
2. Freeze ESR code mappings and marketing-year semantics from official definitions and response evidence.
3. Fetch data by commodity and marketing year, handling pagination or response limits if the verified endpoint requires them.
4. Preserve weekly sales, shipments, accumulated exports, outstanding sales, units, and all additional relevant official indicators without conflating them.
5. Add public function, CLI, schema, validation, and complete-partition refresh hooks.
6. Acquire development and holdout official responses and independent reference observations.

**Concrete deliverables:** ESR adapter and schema; ESR dictionaries; `docs/export_sales.md`; successful redacted live-run evidence; sample CSV; `test/phase_04/`.

**Accuracy and acceptance tests:**

| ID | Test and exact expected outcome |
|---|---|
| P04-A1 | Authenticated live dictionary and numeric requests succeed; actual JSON field names and response completeness are documented. Missing access produces a blocked result, not an empty successful DataFrame. |
| P04-A2 | At least 30 independently read metric values cover at least three commodities, two destinations, and two marketing years; all dimensions, units, and values match pinned official responses. |
| P04-A3 | A week near a marketing-year boundary maps to the correct source marketing year and week-ending date; report release date remains separate. |
| P04-A4 | A real negative net-sales example is retained if available; an explicitly synthetic cancellation case also verifies signed values are not clamped to zero. |
| P04-A5 | Full fixture record counts match the API payload after documented filtering. Unknown codes and truncated/incomplete responses fail visibly. |
| P04-A6 | A holdout commodity/year response passes without changing expectations. Function/CLI results and CSV reload are equal. |
| P04-A7 | A simulated earlier-year revision causes the entire affected configured partition to be refreshed; a deleted source row disappears only from the latest view, while the previous snapshot survives. |

**Commands:** Phase 04 offline/live suites; a small `fetch --dataset export-sales --commodities corn,soybeans,wheat --market-years <verified-years>` run. The key must be supplied through the environment, not command arguments.

**Exit gate:** All seven checks pass, including real authenticated requests. Offline mocks alone cannot complete this phase.

**Phase 05 — Shared PSD data layer**

**Entry requirements:** Phase 01 passed; valid API access for mandatory live checks.

**Implementation tasks:**

1. Verify the PSD endpoint definitions and response schemas; acquire dictionaries for commodities, countries, attributes, and units.
2. Build the union of commodities/attributes required by the three report families and freeze the resulting scope inventory.
3. Fetch each commodity/year partition once and expose country/region/world classifications explicitly.
4. Preserve source period labels, units, and current-revised provenance. Store captures without claiming unavailable historical publication vintages.
5. Implement `download_psd`, CLI support, schema, and caches shared by report datasets.
6. Document when a world total is provided by the source versus a derived calculation. Never add a world total to its member countries.

**Concrete deliverables:** PSD adapter/schema; versioned dictionaries; report-family commodity union; `docs/psd.md`; sample observations; `test/phase_05/`.

**Accuracy and acceptance tests:**

| ID | Test and exact expected outcome |
|---|---|
| P05-A1 | Authenticated live dictionary and observation requests succeed and response completeness is verified. |
| P05-A2 | At least 40 independently read values span grain, oilseed, meal/oil, multiple countries, two years, and several attributes available in the source; values and dimensions match pinned responses. |
| P05-A3 | Country, region, and world rows remain distinct, and the same commodity/year requested through multiple report families is fetched only once per refresh operation. |
| P05-A4 | Source unit codes and scales survive normalization. Any optional conversion has an independently calculated expectation and never overwrites the original unit/value. |
| P05-A5 | A source-defined balance identity is checked for at least two valid commodity/country/year combinations; components and rounding assumptions are documented. No invalid calendar/marketing-year identity is imposed. |
| P05-A6 | A holdout response and a synthetic missing-attribute case behave correctly; unsupported attributes are not fabricated as zero. |
| P05-A7 | Current revised observations are labeled as such; retrieval time is not substituted for report release time or used to claim historic availability. |
| P05-A8 | Python/CLI outputs and CSV reload match; complete-partition updates preserve older snapshots. |

**Commands:** Phase 05 offline/live suites; a small PSD fetch through the internal public function and the implemented dataset/CLI path.

**Exit gate:** All eight checks pass. The shared data layer is complete; this does not yet mean the three report datasets have passed Phase 06.

**Phase 06 — Three FAS report datasets and report reconciliation**

**Entry requirements:** Phase 05 passed.

**Implementation tasks:**

1. Inventory required numerical table families for World Agricultural Production, Grain: World Markets and Trade, and Oilseeds: World Markets and Trade.
2. Define mappings to PSD commodity/attribute/unit/period combinations and document report-specific interpretations.
3. Discover and archive available report attachments with publication dates, titles, URLs, and hashes.
4. For required tables not represented in PSD, seek official structured files first, then implement focused report extraction if necessary. Do not broaden this into general narrative extraction.
5. Expose all three dataset IDs through `download_dataset` and the CLI; expose report manifests through `download_reports`.
6. Create `report_coverage.csv` identifying `psd_mapped`, `separate_extraction`, `source_unavailable`, or `unresolved` for each required table family. Freeze required versus optional distinctions before final testing.

**Concrete deliverables:** Three report mappings; report downloader/catalog; coverage manifest; schemas for any supplementary observations; three source-specific documentation files; `test/phase_06/`.

**Accuracy and acceptance tests:**

| ID | Test and exact expected outcome |
|---|---|
| P06-A1 | At least two report dates per family, including a holdout, are archived correctly; embedded report dates match manifest dates and file hashes. |
| P06-A2 | At least 10 independent report cells per family per date are reconciled, for a minimum of 60 cells. Report-cell extraction matches its report; comparison to PSD is numerical only for aligned vintages and otherwise records a demonstrated vintage difference. |
| P06-A3 | Every required table family has a working numeric extraction/mapping or proven source unavailability. There are zero unresolved mappings for available required tables; narrative-only or optional omissions are explicitly labeled. |
| P06-A4 | Same-vintage discrepancies, unit mistakes, and country/period mismatches fail rather than being dismissed as revisions. Tests include one deliberate mismatched-vintage example that cannot enter a same-vintage comparison. |
| P06-A5 | All three dataset APIs and CLIs return the correct subsets without duplicate PSD observations; any derived metric documents its formula, source inputs, and tolerance. |
| P06-A6 | A changed PDF layout or missing required table triggers a coverage failure, not an apparently successful empty extraction. Historical reports are not backfilled with today's revised PSD values under old report dates. |

**Commands:** Phase 06 offline/live suites; a small run for each dataset with `--with-reports` and separate report-date and marketing-year options.

**Exit gate:** All six checks pass for all three families. A report PDF on disk and a generic PSD download are insufficient without verified mappings and numerical coverage.

**Phase 07 — RMA Summary of Business**

**Entry requirements:** Phase 01 passed; public RMA fixtures and official layouts available.

**Implementation tasks:**

1. Discover annual State/County/Crop/Coverage Level ZIP files and applicable layout documents.
2. Validate ZIP members and decode/parse the verified delimiter, field count, and layout by year.
3. Preserve complete grouping dimensions, source code strings, quantity types, monetary scales, policy counts, and signed values allowed by the source.
4. Implement bounded-memory reading, annual partition output, public function, CLI, and dictionary/schema documentation.
5. Implement a layout-supported `--all-history` boundary and explicit reporting for unsupported earlier layouts.
6. Document safe aggregation levels; do not sum overlapping policy groups or label every quantity as acres.

**Concrete deliverables:** RMA adapter/schema; layout-to-year mapping; `docs/rma_sob.md`; annual sample CSVs; quantity-type dictionary; `test/phase_07/`.

**Accuracy and acceptance tests:**

| ID | Test and exact expected outcome |
|---|---|
| P07-A1 | Live discovery fetches a valid ZIP and applicable layout; every data member has the expected fields or a documented supported layout. |
| P07-A2 | At least 30 independent field values across two years, two geographic areas, and multiple plan/coverage categories match the official text/layout. Include quantities, money, and counts. |
| P07-A3 | Leading-zero geographic codes and source quantity types are preserved. At least one non-acre type is verified if present in scope; otherwise a synthetic case tests the branch without claiming real-source coverage. |
| P07-A4 | Source rows and normalized rows reconcile with documented filters; full business keys are unique or source duplicates are explicitly investigated, never silently dropped. |
| P07-A5 | At least two independently calculated, non-overlapping partition subtotals for money and quantity agree with normalized output at source precision. State-level totals must not be added to member-county rows. |
| P07-A6 | A holdout older layout/year passes; malformed row width and unknown layout fail before publication; signed monetary adjustments are preserved where permitted. |
| P07-A7 | A small Python/CLI request and schema-guided CSV round-trip match; a deliberately bounded chunk size produces the same result as a small in-memory reference. |

**Commands:** Phase 07 offline/live suites; a small `fetch --dataset rma-sob --commodity-years <verified-years>` run.

**Exit gate:** All seven checks pass. Acreage-only naming or a partial dimension key is a blocking error.

**Phase 08 — Revision handling, release calendars, and recovery**

**Entry requirements:** Phases 02, 03, 04, 06, and 07 passed for final integration. Shared components may be developed earlier.

**Implementation tasks:**

1. Implement `sync` across sources with persisted partition state and complete-version publication.
2. Refresh configured historical partitions when source revisions can affect them. Do not assume only the newest week/year changes.
3. Make source release rules configurable from verified evidence. Separate report availability, API updates, and historical-file updates.
4. Preserve date-only/unknown-time precision. Convert known official Eastern times using `America/New_York`, store UTC, and display Asia/Shanghai only as a presentation option.
5. Implement bounded retries, delayed-release status, resumable tasks, and atomic export-manifest switching.
6. Provide a deterministic clock and mock source versions for update tests. Do not wait for a real future release to test the state machine.

**Concrete deliverables:** `sync`, calendar functionality, persisted run/partition state, update documentation, recovery playbook, `test/phase_08/`.

**Accuracy and acceptance tests:**

| ID | Test and exact expected outcome |
|---|---|
| P08-A1 | A version-B fixture adds a row, changes a value, and removes a row. Latest output equals B exactly; version A remains reproducible. |
| P08-A2 | An earlier-year revision is detected within the configured refresh policy and a changed source at an unchanged URL is not missed. |
| P08-A3 | Repeating a successful unchanged job creates no duplicate business records or redundant normalized snapshot; the check itself is still logged. |
| P08-A4 | Inject failures before download completion, after normalization, and before manifest publication. Resume completes correctly without exposing partial output or advancing a failed partition's watermark. |
| P08-A5 | If one required partition fails, the run is partial/nonzero; the previous complete export remains selected. Resume produces the same result as a clean full run. |
| P08-A6 | For fixed clock tests, 2026-01-15 12:00 America/New_York converts to 17:00 UTC, and 2026-07-15 12:00 converts to 16:00 UTC. A date-only source produces no invented timestamp. These dates are timezone tests, not asserted USDA release dates. |
| P08-A7 | A shifted holiday release and a delayed artifact follow the saved official event, not a hard-coded weekday; a stale calendar is labeled stale. |
| P08-A8 | An API partition can be available while its report is pending; the manifests preserve both statuses. Unknown freshness is never reported as confirmed up to date. |
| P08-A9 | Real small-source checks exercise update discovery; finite retries and clear failure status remain intact when a source is unavailable. |

**Commands:** Phase 08 offline/live suites; `python -m usda_data sync --dataset all --config config/datasets.toml` against a small test configuration and isolated output root.

**Exit gate:** All nine checks pass. Actual unattended scheduler installation is not required and is not performed.

**Phase 09 — Full backfill, coverage, and data acceptance**

**Resource budget amendment (November 17, 2026):** User-authorized full-backfill peak-memory budget is 1 GiB (1,024 MiB), configured in `config/full_backfill.json`, superseding the initial 512 MiB setting. P09-A6 retains its measured-memory and chunk-invariance requirements. Earlier measurements and failures remain archived; only the resource threshold changes.

**Entry requirements:** Phase 08 passed; frozen full-scope configuration and real credentials available.

**Implementation tasks:**

1. Discover currently available periods and expand the complete task inventory. Record a run cutoff and source versions so the job does not silently become a moving target.
2. Enumerate all in-scope partitions before executing them. Report estimated requests, file sizes when known, and local storage needs.
3. Backfill from the configured starting period using bounded concurrency, checkpoints, and disk-backed partitions.
4. Validate every partition and produce a complete coverage manifest, including evidence for source-supported gaps.
5. Perform independent, stratified audits across every dataset, including early, middle, and recent periods, available layout variants, and non-default commodities/regions.
6. Repeat an unchanged check and a deliberate interruption/resume trial on a representative subset.
7. Publish a complete export manifest only when all required partitions pass their checks.

**Concrete deliverables:** Raw archives; normalized/versioned partitions; seven dataset exports; report archive; `coverage_manifest.csv`; reconciliation and gap reports; `test/phase_09/`; complete backfill run manifest.

**Accuracy and acceptance tests:**

| ID | Test and exact expected outcome |
|---|---|
| P09-A1 | Expected partitions equal succeeded plus evidenced source-unavailable partitions. Pending, failed, unexplained missing, and silently dropped partitions are all zero. |
| P09-A2 | Full-table validation finds zero unexplained duplicate keys, missing required dimensions, unknown units, and unaccounted parser losses. |
| P09-A3 | At least 20 additional independently checked numeric cells per dataset, distinct from development references, pass; minimum 140 checks across the seven datasets. Selection is stratified and frozen before inspecting results. |
| P09-A4 | Earliest/latest coverage and every gap are reconciled with the source inventory. An API's lack of historical vintages is reported separately from availability of historical observation years. |
| P09-A5 | Full exports reference exact partition hashes and versions; repeated unchanged processing and subset resume produce identical canonical business data, ignoring run timestamps. |
| P09-A6 | Memory use remains within a documented configured budget by partitioning/chunking; a deliberately small test chunk size changes neither counts nor values. |
| P09-A7 | All three FAS report families have attachment inventories and structured coverage maps across observed layout families; unresolved available required tables are zero. |

**Commands:** Full `fetch --dataset all --config config/datasets.toml --resume`, full `validate`, and Phase 09 offline/live tests. Save exact commands and full summaries; do not write a generic claim that the download succeeded.

**Exit gate:** All seven checks pass. Small samples, placeholders, and API mocks cannot substitute for the configured full backfill.

**Phase 10 — Interface, SQL portability, and handover acceptance**

**Entry requirements:** Phase 09 passed.

**Implementation tasks:**

1. Verify package installation and documented examples in a clean environment.
2. Finalize all public functions, CLI help, validation errors, exit codes, and English documentation.
3. Ship field dictionaries, machine-readable schemas, CSV-reader examples, and a local database import example.
4. Validate every exported business-table shape in an isolated local SQL database. Do not connect to production.
5. Document publication schedules, units, economic interpretation, revisions, version limitations, credentials, recovery, and known source gaps.
6. Assemble the final evidence index and checklist covering all original internship requirements.

**Concrete deliverables:** Installable package; README; documented Python/CLI examples; schema files; database import example; release/schedule notes; acceptance index; final dataset manifest; `test/phase_10/`.

**Accuracy and acceptance tests:**

| ID | Test and exact expected outcome |
|---|---|
| P10-A1 | Clean installation and all documented minimal examples run successfully using the declared supported runtime and dependency constraints. |
| P10-A2 | Each of the seven dataset IDs has working Python and CLI access; corresponding outputs are equal after canonical sorting and metadata handling. |
| P10-A3 | CSV-to-SQL-to-readback preserves row counts, keys, nulls, code strings, dates, and numeric values for every schema. Use a documented exact-decimal strategy; SQLite tests may use scaled integers for declared fixed-scale amounts rather than relying on floating-point affinity. |
| P10-A4 | SQL key constraints reject a deliberately inserted duplicate; missing required fields are rejected. Derived hash keys do not hide missing business dimensions. |
| P10-A5 | CLI exits 0 for success/confirmed unchanged, 1 for runtime or partial failures, and 2 for invalid arguments. Authentication failure is never a successful empty export. |
| P10-A6 | All mandatory test suites pass; all required live checks have saved real evidence. Zero-test runs and skipped required checks cannot satisfy the final gate. |
| P10-A7 | The final ledger, schemas, data manifests, docs, and source-registry claims agree; no unresolved required coverage defects or unverified completion statements remain. |

**Commands:** Clean-environment install; the Phase 00 inventory verifier; `python -m pytest -m 'not live' -q`; the required bounded live suites; local SQL import/readback command; all README examples.

**Exit gate:** All seven checks pass. Deliver links to code, data, documentation, and the acceptance evidence index, plus a factual summary of any source-supported limitations.

**6. Required CLI behavior**

Implement these commands incrementally with their source phases:

```text
usda-data list-datasets
usda-data calendar --dataset DATASET
usda-data fetch --dataset DATASET [source-specific range options]
usda-data fetch --dataset all --config config/datasets.toml --dry-run
usda-data fetch --dataset all --config config/datasets.toml --resume
usda-data sync --dataset all --config config/datasets.toml
usda-data validate --input-dir PATH
```

Also support `python -m usda_data` with identical behavior. Range options must retain their source meanings:

| Option | Meaning |
|---|---|
| `--start`, `--end` | Inclusive WASDE report-date bounds |
| `--market-years` | ESR/PSD source marketing-year identifiers |
| `--years` | ERS observation years |
| `--commodity-years` | RMA commodity years |
| `--report-start`, `--report-end` | Inclusive FAS report archive bounds |
| `--with-reports` | Archive requested report families as well as structured data |
| `--data-dir` | Root for raw files, state, normalized data, and reports |
| `--output-dir` | Location for user-facing exports |
| `--all-history` | Discover all history supported by implemented source layouts |
| `--force` | Refetch without deleting previous archives |

`--dry-run` may fetch discovery metadata, but must not retrieve full numeric datasets. State that behavior in help. `--dataset all` reads separate source ranges from configuration rather than overloading a single ambiguous year option.

**7. Phase-close report template**

Use this template in each evidence directory and summarize it to the user when closing a phase:

```text
Phase:
Status:
Scope/configuration hash:
Code revision or source-tree hash:
Deliverables created or updated:
Mandatory test IDs passed / failed / blocked:
Commands and exit codes:
Official artifacts and SHA-256 references:
Independent numerical comparisons performed:
Coverage and row-count reconciliation:
Known source limitations:
Implementation defects still open:
External blockers:
Next eligible phase and exact next action:
```

If work resumes in a later Codex session, read this document, the execution ledger, and the last phase summary before editing. Reuse completed evidence unless source, configuration, or relevant code changes invalidate it. Re-run affected checks rather than restarting all work automatically.

**Appendix A — Official source-discovery starting points**

These URLs were carried forward from the companion plan. Reverify them in Phase 00. Discover current attachments from official landing pages and save evidence; a reachable URL alone does not establish correctness. Source publication conventions must be checked against current official pages before scheduling.

| Source | Starting point |
|---|---|
| WASDE | `https://www.usda.gov/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report` |
| FAS API portal | `https://apps.fas.usda.gov/opendataweb/home` |
| FAS API specification | `https://apps.fas.usda.gov/opendatawebv2/assets/swagger/swagger.json` |
| FAS API host | `https://api.fas.usda.gov` |
| FAS export sales program | `https://www.fas.usda.gov/programs/export-sales-reporting-program` |
| FAS World Agricultural Production | `https://www.fas.usda.gov/data/world-agricultural-production` |
| FAS Grain: World Markets and Trade | `https://www.fas.usda.gov/data/grain-world-markets-and-trade` |
| FAS Oilseeds: World Markets and Trade | `https://www.fas.usda.gov/data/oilseeds-world-markets-and-trade` |
| ERS costs and returns | `https://www.ers.usda.gov/data-products/commodity-costs-and-returns` |
| ERS methodology | `https://www.ers.usda.gov/data-products/commodity-costs-and-returns/documentation` |
| RMA SOB files and layouts | `https://www.rma.usda.gov/tools-reports/summary-of-business/state-county-crop-summary-business` |

API paths and publication times belong in the verified source registry, not immutable assumptions in parser code. The inherited timing hypotheses are: WASDE monthly noon ET; its consolidated CSV the following day; ESR usually Thursday morning ET; separate PSD and FAS report availability; ERS periodic estimate/forecast updates; and RMA recent-year weekly refreshes. Exact times, holiday changes, layout dates, and API authentication must be established from current evidence before their dependent phases pass.

**Appendix B — Initial instruction for an implementation session**

```text
Implement USDA_DATA_PHASED_EXECUTION_PLAN_EN.md in this repository.
Read repository instructions, inspect existing work, and begin with Phase 00
or the first eligible incomplete phase in docs/execution_status.md.
For each phase, produce the listed deliverables, execute every mandatory
acceptance test, and save independently sourced accuracy evidence.
Do not mark blocked, skipped, mocked-only, or partially covered work as passed.
Continue independent phases when an external dependency is unavailable.
Maintain the execution ledger and report the next concrete action.
```
