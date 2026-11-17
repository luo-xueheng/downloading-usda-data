**USDA Data Acquisition Project: Complete Implementation Plan**

Version: v1.0  
Research date: 2026-11-12 (Asia/Shanghai)  
Scope: the 7 datasets listed in the supplied screenshot  
Document status: implementation proposal. Functions, commands, directories, and field names are proposed designs; API authentication tests, sample parsing, and downloader development have not yet been completed.

**1. Project Goals and Delivery Criteria**

Build a rerunnable Python data acquisition package covering "official data discovery → download → raw-file archiving → cleaning and validation → DataFrame/CSV output → subsequent updates."

| Internship requirement | Concrete project deliverable | Completion criterion |
|---|---|---|
| Understand release timing | Release rules, official calendar entry points, timezones, and retrieval strategies | Distinguish report release time, data update time, and actual retrieval time |
| Prefer APIs | FAS ESR and PSD API downloaders; official structured files for other sources | Authentication and real API requests pass; file download links can be discovered automatically |
| Understand economic meaning | Dataset documentation, measure dictionaries, units, and measurement definitions | Explain every column, row granularity, and main usage limitations |
| Provide public Python functions | Importable download functions | Return pandas DataFrames without requiring callers to use a terminal |
| Provide a CLI | A unified `usda-data` command | Parameters control dataset, scope, output, and update behavior |
| Modularize | Shared networking, storage, and validation modules, plus separate source modules | A change in one source does not require rewriting every downloader |
| Support SQL ingestion | Fixed fields, types, unique keys, CSVs, and schema files | Values, nulls, and codes remain consistent when CSVs are read back using declared types |

This phase covers data acquisition and delivery, not production database deployment, trading strategies, visualization websites, or actually deployed scheduled jobs. It provides scheduling documentation and commands that schedulers can invoke.

**2. Data Scope and Default Decisions**

| User-requested item | Internal dataset name | Underlying download module | Output form |
|---|---|---|---|
| WASDE | `wasde` | `wasde` | Supply/use observations and original CSV/Excel/XML files |
| Export Sales | `export-sales` | `fas_esr` | Weekly export sales table and original JSON |
| World Agricultural Production | `world-production` | `fas_psd` + `reports` | PSD production-measure view, original monthly reports, and report catalog |
| Grain: World Markets and Trade | `grain-trade` | `fas_psd` + `reports` | PSD grain-measure view, original monthly reports, and report catalog |
| Oilseeds: World Markets and Trade | `oilseed-trade` | `fas_psd` + `reports` | PSD oilseed/meal/vegetable-oil measure view, original monthly reports, and report catalog |
| Commodity Costs & Returns | `costs-returns` | `ers_costs_returns` | Long-format costs and returns table and original CSV/XLSX files |
| RMA Summary of Business | `rma-sob` | `rma_sob` | Insurance business summary table, original ZIPs, and record-layout files |

Use **5 types of numeric-data downloaders + 1 shared report-archiving module**. The three FAS monthly reports share PSD download results and produce their respective views through configuration; the same PSD record is not downloaded or inserted into the database multiple times.

The following defaults can be changed in configuration before implementation and do not block starting work:

- Initial acceptance backfill: from 2010 through the latest data available at runtime; historical WASDE CSV coverage starts in April 2010.[S01][S02]
- `--all-history` extends to the earliest year actually available from each source and produces a coverage manifest; identical historical depth across sources is not promised.
- Formal acquisition covers all commodities and regions within the configured scope. Corn, soybeans, and wheat are only initial integration samples, not substitutes for complete delivery.
- WASDE covers parsable structured tables in the selected official files; initial integration may start with crop tables, but final coverage must document livestock and other tables as well.
- ERS scope includes Recent and Historical costs and returns and cost-forecast files on the main product page, retaining subdivisions such as enterprise types; separately linked Organic products are excluded for now.
- RMA uses the State/County/Crop/Coverage Level files in this phase. Cause of Loss, FSA prevented planting, and more detailed RMA Type/Practice/Unit files are excluded for now.
- Previously completed NASS Crop Progress & Condition and Crop Production work will not be redeveloped.
- Retain raw data and versions from subsequent retrievals; explicitly mark unavailable historical release vintages rather than presenting the latest revised values as values known at the time.

**3. Confirmed Facts and Items Requiring Verification**

The following official materials have been reviewed; source identifiers appear at the end. Confirming a download entry point does not mean the downloader has already run successfully.

| Item | Confirmed | Still to verify during implementation |
|---|---|---|
| WASDE | Official consolidated historical CSV and current structured files; monthly releases [S01] | Headers, footnotes, merged cells, and special values across years; mapping between current files and the historical CSV |
| ESR | The current portal requires an api.data.gov key; API documentation provides commodity, country, unit, and data paths [S03][S04] | Response fields, historical coverage, empty-response meaning, and rate limits using a real key |
| PSD | Supports measures by commodity, country, and marketing year [S04] | Coverage relationship between report tables and API measures; historical depth and release-time information precision for each commodity |
| FAS monthly reports | Official release schedules list all three reports [S06] | Discovery of historical attachment links; which tables PSD can reconstruct exactly |
| ERS | The main page provides CSV/XLSX files; documentation describes release frequency [S08][S09] | Alignment of historical and recent definitions, units in each file, and forecast-file layouts |
| RMA | Official annual ZIPs, delimited text, and record layouts are available [S10][S11][S12] | Actual ZIP members, field counts, encoding, and layout applicability across years |

This research did not establish a more suitable dedicated public API for WASDE, this ERS product, or RMA SOB. The plan prioritizes the confirmed official structured files; this is not a claim that no APIs exist.

**4. Release Calendar and Retrieval Timing Design**

Interpret official times using `America/New_York`, store database timestamps in UTC, and optionally display `Asia/Shanghai` to users. When the exact time is unknown, retain the date and a precision flag rather than inventing 00:00 or a fixed minute.

| Data/file | Official release pattern | Proposed checking strategy | Basis |
|---|---|---|---|
| Current WASDE report | Official monthly calendar, 12:00 ET | Start checking 5 minutes after release; retry failures or stale files with backoff | [S01] |
| Consolidated historical WASDE CSV | Updated the day after the report release; exact minute unspecified | Start checking the next day; keep waiting if content is unchanged, and alert after the expected window | [S01] |
| ESR | Usually Thursday at 08:30 ET; announcements and holidays may change this | Read the official schedule, then check API update markers and data after release | [S05] |
| PSD grains, oilseeds, etc. | The official production report states that relevant PSD data update at 12:00 ET on WASDE release days | After 12:00, check update metadata for the relevant commodities; do not assume every commodity updates together | [S07] |
| Three FAS monthly reports | The current official calendar schedules them for 12:15 ET | Check report attachments independently; successful PSD retrieval does not establish successful report archiving | [S06] |
| ERS annual costs and returns | Preliminary estimates in the first week of May; final estimates in the first week of October | Prefer each file's Next Update; check on the planned date and retain low-frequency polling | [S08][S09] |
| ERS cost forecasts | Usually mid-June and mid-November | Track separately from annual estimates; use file pages for exact dates | [S09] |
| RMA SOB | The most recent five years usually refresh on Monday mornings, with no exact minute | Start checking at noon ET on Mondays; first verify whether bulk ZIPs update at the same time | [S10] |

"Five minutes after release" and "check at noon" above are engineering settings, not USDA availability guarantees. Report posting, file replacement, and API updates may occur at different times; verify content and versions.

Create a `release_calendar` table with at least:

```text
source, dataset, artifact_kind, event_id,
expected_release_date, expected_release_at_utc, source_timezone,
time_precision, calendar_url, checked_at_utc, status
```

`artifact_kind` distinguishes report, api, and historical_csv. `status` distinguishes scheduled, available, delayed, cancelled, and unknown. If calendar retrieval fails, retain old records and mark them stale; do not invent the next release date.

**5. Source-Specific Download Implementation Plans**

**5.1 WASDE**

Primary use: organize supply/use estimates from successive releases to support analysis of production, use, trade, ending stocks, and revisions. Write measure explanations for each commodity and table.[S01][S02]

Implementation steps:

1. Discover historical CSV and current-file links from the official main page; save the original page, final download URL, and file hash.
2. Build the historical master table from the consolidated CSV, retaining report issue, data year, table identifier, and all grouping dimensions.
3. Add current Excel/XML parsers for release-day acquisition; test samples and choose the more stable format as the primary path.
4. When the historical CSV arrives the next day, compare it with current-file results. Retain discrepancies and provenance rather than silently overwriting conflicting values from the two sources.
5. Save PDFs as reference originals; evaluate dedicated extraction for a table only if a key table has no structured source.

Historical WASDE files retain values as published in each report, while PSD historical series may include subsequent revisions; they are not interchangeable.[S02]

Acceptance: select recent, older-year, and year-transition reports, checking at least 10 data points in each category. Report record counts, table inventories, and cells that failed to parse. Explain every uncovered table in the coverage manifest; do not mark the entire report complete when coverage is incomplete.

**5.2 Export Sales: FAS ESR API**

Primary use: separately track sales contracts, actual exports, and outstanding orders. Net sales, weekly exports, and accumulated exports are different measures; outstanding orders cannot directly substitute for a final export forecast.[S05][S13]

Authentication: use the intern's Nexus company email to request an api.data.gov key through the official FAS entry point; the intern completes email verification. The program reads `USDA_FAS_API_KEY` from the environment and never writes it into source code, logs, or sample CSVs.[S03]

Core request paths have been confirmed in the official Swagger:[S04]

```text
Host: https://api.fas.usda.gov
Header: X-Api-Key: <read from the environment variable>

GET /api/esr/commodities
GET /api/esr/countries
GET /api/esr/unitsOfMeasure
GET /api/esr/datareleasedates
GET /api/esr/exports/commodityCode/{commodityCode}/allCountries/marketYear/{marketYear}
```

Implementation steps: cache dictionaries → build commodity/marketing-year tasks → download all destinations per task → save original JSON → normalize fields → validate and publish partitions.

Incremental strategy: when a commodity's update marker changes, refetch all configured marketing years for that commodity. Official documentation states that revisions may span multiple years; appending only the latest week would miss changes.[S04] Any later optimization must retain periodic full-scope reconciliation and explicit revision-lag metrics.

Store marketing year, reporting week end date, and release date separately. Configure commodity-year start dates from official definitions rather than assuming calendar years. Allow negative net sales; evaluate other negative values according to their field definitions.

Acceptance: at least 3 commodities, multiple destinations, and marketing-year transition samples; spot checks match official query results; historical revisions and cancelled sales are not incorrectly deleted or set to zero.

**5.3 Three FAS Monthly Reports: PSD Values + Original Reports**

Create configurations matching the business scope of each report:

| View | Initial measure scope | Interpretation focus |
|---|---|---|
| `world-production` | Area, production, and yield, matched item by item to the report | Whether supply changes come from changes in area or yield |
| `grain-trade` | Grain production, supply, consumption, trade, and stocks | Supply/use structures across countries and marketing years |
| `oilseed-trade` | Oilseed, meal, and vegetable-oil production, processing, consumption, trade, and stocks | Distinguish raw materials, processed products, and different units |

These are proposed measures; final coverage depends on checking API dictionaries against report tables. Do not assume every measure exists for every commodity.

Core paths:[S04]

```text
GET /api/psd/commodities
GET /api/psd/countries
GET /api/psd/commodityAttributes
GET /api/psd/unitsOfMeasure
GET /api/psd/commodity/{commodityCode}/country/all/year/{marketYear}
GET /api/psd/commodity/{commodityCode}/world/year/{marketYear}
GET /api/psd/commodity/{commodityCode}/dataReleaseDates
```

Implementation steps:

1. Retrieve dictionaries and build commodity, region, measure, and unit mappings; namespace ESR and PSD codes separately rather than assuming they match.
2. Retrieve each "commodity × marketing year" once, with the three report views sharing the cache.
3. Distinguish aggregation levels for world, regional, and country records; do not double-count regional totals and their member countries.
4. Save a current snapshot whenever the source changes; synchronize original reports and the catalog.
5. Build `report_coverage.csv` for the three reports, including report date, table name, measure, PSD mapping, match status, and discrepancy reason.
6. For numeric tables without a PSD match, first look for official downloadable tables; implement dedicated extraction if needed. Archiving a PDF alone does not establish that its numeric tables have been structured.

The current historical series from PSD cannot automatically reconstruct past monthly release vintages. Mark the initial backfill as a "current revised series" and accumulate local snapshots in subsequent runs. Exact historical release vintages require a separate report-archive extraction task.[S02]

Acceptance: select at least 2 issues of each of the three reports and check at least 10 mappable data points per report. Explain discrepancies due to timing, units, year definitions, or revisions; a report adapter is incomplete if key numeric tables remain uncovered.

**5.4 ERS Commodity Costs & Returns**

Primary use: compare production-cost components and returns. Distinguish cost items, return items, output, and prices, as well as per-acre and per-unit-of-product bases. Official sources distinguish Recent, Historical, and forecast series, with changes in historical methodologies and regional definitions.[S08][S09]

Implementation steps:

1. Enumerate download files from the product page, recording commodity, subseries, format, Last Updated, and Next Update.
2. Prefer CSV parsing and cross-check with XLSX when needed; if a forecast is only available in Excel, use the corresponding parser.
3. Reshape year columns into long format; if the source is already long-format, normalize it directly through field mappings.
4. Retain commodity, enterprise type, region, year, accounting item, unit, methodology period, and data status.
5. Retain overlapping Recent/Historical periods separately; do not deduplicate solely because year and commodity match.
6. Reprocess the complete file whenever it changes, retain the previous version, and report counts of added, modified, and deleted records.

`series_family` distinguishes recent, historical, and forecast; `estimate_status` separately distinguishes preliminary, final, and unknown. Do not interpret recent as "forecast" or infer that a row is final solely from the current month.

Acceptance: cover all in-scope files on the main page; spot-check crops, livestock, historical methodologies, forecasts, and different enterprise types; preserve correct units and nulls; check total-cost relationships only where official definitions explicitly support addition.

**5.5 RMA Summary of Business**

Primary use: examine insurance participation, premiums, liability, and indemnities. Quantity fields may represent area, weight, or another quantity; interpret them together with Quantity Type.[S12]

Implementation steps:

1. Discover annual State/County/Crop/Coverage Level ZIPs and their Record Layouts from the official page.
2. Save the ZIP, layout version, and hashes; parse using the `|` delimiter and layout rather than treating the file as comma-separated CSV.[S11]
3. Use the layout to identify dimensions such as year, state/county codes, crop, insurance plan, coverage category, delivery type, and coverage level.[S12]
4. Handle monetary amounts, quantities, and policy counts separately; retain original missing-value markers and quantity types.
5. Implement the layout for 1989 onward first; backfill from 2010 by default, with `--all-history` extending to the earliest year available under that layout. Treat the 1948–1988 layout as a separate historical extension, not directly concatenated with the newer layout.[S11]
6. Routine updates refresh the most recent five years specified by the official source and detect newly available annual files; check older years less frequently.[S10]

The official page's "Monday update" statement refers to the SOB product. Implementation must verify ZIP update timing and content changes; if bulk files lag, record the actual delay rather than presenting a page refresh time as a file release time.

Acceptance: spot-check recent and older years and different insurance plans; verify field counts and aggregation definitions; preserve leading zeros in state/county codes; do not rename all quantities to acres. The official layout allows signed indemnity amounts, so a blanket "all numbers must be nonnegative" rule is inappropriate.[S12]

**6. DataFrame and Future SQL Table Design**

The following are proposed fields, not original official fields. After obtaining samples in Phase A, complete the field-by-field mappings, types, nullability, units, enumerations, and provenance. Do not invent values with uncertain meaning to fill missing fields.

**6.1 Common Conventions**

| Field/convention | Design |
|---|---|
| Naming | English `snake_case`; explanatory text belongs in the field dictionary |
| Codes | Use strings; preserve leading zeros and source-specific namespaces |
| Years | Use `marketing_year`, `calendar_year`, and `commodity_year` separately rather than overloading one `year` field |
| Dates | `YYYY-MM-DD`; exact timestamps use ISO 8601 with a UTC indicator |
| Values | Retain `raw_value` and nullable numeric columns; derive monetary precision from source files and avoid unnecessary decimal rounding |
| Missing values | Keep missing values distinct from zero; use `value_status` for established meanings such as unavailable, suppressed, and not_applicable |
| Units | `unit_code`, `unit_label`, and scale where needed; conversions create additional columns only |
| Provenance | `source`, `source_artifact_id`, `schema_version` |
| Versions | `snapshot_id`, `content_hash`, `retrieved_at_utc` |
| Release time | `source_release_date`, nullable `source_release_at_utc`, `release_time_precision` |
| Source vintage type | `vintage_type` distinguishes published_report, current_revised, and captured_snapshot |

DataFrames use nullable string, integer, and numeric types and explicit temporal types. Declare future SQL types in schemas as logical types such as TEXT, INTEGER/BIGINT, NUMERIC/DOUBLE, DATE, and TIMESTAMP, with target-database adaptation notes. CSVs do not carry types themselves, so accompanying schema files and reading examples are required.

**6.2 Business Table Granularity and Candidate Unique Keys**

| Table | Row granularity | Core business fields | Candidate unique key, excluding version |
|---|---|---|---|
| `wasde_observations` | A measure within a fully specified grouping in one report issue | Report date, table identifier, commodity, region, year, measure, classifications, value, unit, footnotes | Report date + table identifier + commodity + region + year + measure + all classification dimensions + unit |
| `esr_weekly_sales` | A reporting week, commodity, destination, and marketing year | Week end date, commodity code, country code, marketing year, unit, sales/export measures | Commodity + country + marketing year + week end date + unit, plus any other actual grouping fields found in samples |
| `psd_observations` | A region, commodity, marketing year, and measure | Commodity code, region code, geographic level, marketing year, measure code, value, unit | Commodity + region + geographic level + marketing year + measure + unit |
| `ers_costs_returns` | An annual item under one accounting basis | Commodity, enterprise type, region, year, series, methodology period, accounting item, value, unit | Commodity + enterprise type + region + year + series + methodology period + accounting item + unit |
| `rma_sob` | One insurance summary under the complete official grouping | Crop year, state/county, crop, insurance plan, coverage category, delivery type, coverage level, quantity type, amounts, and quantities | Year + state/county + crop + insurance plan + coverage category + delivery type + coverage level + quantity type, verified against the layout |

Freeze primary keys after sample verification. If a candidate key conflicts, first look for missing business dimensions; do not hide the issue with `drop_duplicates()` or row numbers. The archive table's unique key is "complete business key + snapshot_id." A stable `observation_key` hash may be created, but retain the original dimensions used to construct it.

Proposed standardized ESR measures include net sales, weekly exports, accumulated exports, outstanding sales, and related measures supplied by official responses; verify each column's meaning using samples and official documentation. RMA will retain policy counts, quantity types and net reported quantities, liability, premiums, subsidies, indemnities, and related fields, with complete mappings based on the layout.[S12][S13]

**6.3 Supporting Tables**

- `source_artifacts`: Download URL, file type, file hash, raw path, retrieval time, HTTP metadata, official date, and precision.
- `report_documents`: Report type, report date, title, attachment URL, local path, and hash.
- `report_coverage`: Mappings from report tables to numeric fields and coverage status.
- `download_runs`: Tasks, parameters, start/end times, status, row counts, failed partitions, and versions.
- `coverage_manifest`: Expected and actual commodity/year/region partitions, earliest and latest dates, gaps, and reasons.
- `release_calendar`: See Section 4.
- Commodity, region, measure, and unit dictionaries: store separately by source, with separate mappings for cross-source relationships.

**7. Module and Directory Design**

```text
usda-data/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── config/
│   ├── datasets.toml
│   ├── commodities.toml
│   └── report_mappings.toml
├── src/usda_data/
│   ├── __init__.py              # Export public functions
│   ├── __main__.py              # python -m usda_data
│   ├── api.py                   # Public interface and parameter validation
│   ├── cli.py                   # CLI argument parsing
│   ├── config.py
│   ├── http.py                  # Timeouts, rate limits, retries, and redaction
│   ├── storage.py               # Files, CSV, and atomic publication
│   ├── state.py                 # Download manifests, checkpoints, and update watermarks
│   ├── validation.py
│   ├── calendar.py
│   └── sources/
│       ├── wasde.py
│       ├── fas_esr.py
│       ├── fas_psd.py
│       ├── ers_costs_returns.py
│       ├── rma_sob.py
│       └── reports.py
├── schemas/                    # Fields, types, keys, and null rules
├── docs/                       # Sources, economic meaning, release times, and usage guides
├── test/fixtures/             # Small official samples and representative exceptional cases
└── data/
    ├── raw/                    # Original files/responses archived by source and version
    ├── normalized/             # Normalized partitions and snapshots
    ├── exports/                # User-facing CSVs
    ├── reports/                # Original monthly reports
    └── manifests/              # Coverage, validation, and run records
```

Dependency approach: use pandas for the DataFrame interface, choose one HTTP client, and prefer standard-library `argparse` for the CLI; add Excel/XML parsing dependencies based on verified formats. Pin verified Python and dependency versions in Phase A and provide installation instructions, avoiding simultaneous maintenance of multiple networking or CLI frameworks.

Each source module owns `discover → fetch → parse → normalize → validate`. Shared modules handle network retries, logging, CSV output, and versioning. The CLI only handles arguments, calls public functions, and displays results.

**8. Public Python Functions and CLI Contract**

The following interfaces are proposed contracts and are not yet executable.

```python
from usda_data import (
    download_wasde,
    download_export_sales,
    download_psd,
    download_costs_returns,
    download_rma_sob,
    download_dataset,
    download_reports,
)

# Return a normalized pandas.DataFrame; start and end dates are inclusive.
df = download_wasde(start="2020-01-01", end="2026-11-12")

# Map commodity names to official ESR codes through configuration; market_years are not release dates.
esr = download_export_sales(
    commodities=["corn", "soybeans"],
    market_years=[2024, 2025, 2026],
    countries="all",
)

# Generate the three monthly report views through the same PSD data layer.
production = download_dataset(
    "world-production",
    market_years=[2024, 2025, 2026],
)

# Return a report-catalog DataFrame and save attachments to output_dir.
reports = download_reports(
    "grain-trade", start="2026-01-01", end="2026-11-12",
    output_dir="data/reports",
)

df.to_csv("data/exports/wasde.csv", index=False, encoding="utf-8")
```

Documentation for every public function must include parameter types, time-range semantics, returned fields, authentication, caching and disk-write behavior, exception types, and a minimal example. By default, use a shared local cache, archive raw responses, and return normalized DataFrames; control the root directory through configuration. Process large scopes by partition and also provide an iterator interface; the CLI must not require loading all history into one DataFrame.

Proposed CLI:

```bash
# View help and source configuration
usda-data --help
usda-data list-datasets
usda-data calendar --dataset wasde

# Preview the planned download scope without retrieving all numeric data
usda-data fetch --dataset all --config config/datasets.toml --dry-run

# Fetch WASDE by report release date
usda-data fetch --dataset wasde --start 2020-01-01 --end 2026-11-12 --output-dir data/exports

# Fetch ESR by marketing year
usda-data fetch --dataset export-sales --commodities corn,soybeans --market-years 2024,2025,2026 --output-dir data/exports

# Retrieve a monthly report view from PSD and archive report attachments for the specified period
usda-data fetch --dataset grain-trade --market-years 2024,2025,2026 --with-reports --report-start 2026-01-01 --report-end 2026-11-12

# Fetch ERS by observation year and RMA by crop year
usda-data fetch --dataset costs-returns --years 2020:2026
usda-data fetch --dataset rma-sob --commodity-years 2020:2026

# Process all sources using configuration; support recovery of failed partitions
usda-data fetch --dataset all --config config/datasets.toml --resume
usda-data sync --dataset all --config config/datasets.toml
usda-data validate --input-dir data/normalized
```

Parameter semantics: year ranges include both endpoints; `--start/--end` are used only for clearly defined release-date ranges and must not silently mean marketing years for different sources. `--dataset all` uses configuration to define each source's scope separately. Unimplemented or inapplicable parameters must raise errors. `--all-history` extends coverage; `--force` allows refetching but does not delete raw archives.

CLI and Python calls must use the same data pipeline. Exit-code conventions: `0` for complete success or explicitly no updates, `1` for at least one failed task, and `2` for argument/configuration errors. Run summaries list succeeded, unchanged, not_yet_available, and failed; empty CSVs must not conceal authentication failures.

**9. Raw Archives, Updates, Revisions, and Resume**

Use three data layers:

```text
raw: official original files/JSON → normalized: versioned normalized data → exports: CSVs of the latest complete partitions
```

1. Generate a task manifest before the initial backfill, with one resumable task per commodity/year/file and expected, downloaded, validated, and published states.
2. Save SHA-256, provenance, and timestamps for raw files. Identical content may reuse a file, but retain a separate record of each check.
3. After successful download, write a temporary file; publish atomically and update the watermark only after format, field, and partition validation passes.
4. Save a complete new snapshot for each changed partition. Replace that entire partition in the latest view to avoid leaving behind rows deleted by the source, as an upsert-only approach would.
5. Compare old and new partitions and count additions, modifications, and deletions; do not overwrite historical snapshots.
6. If some partitions fail, successful partitions may be retained, but mark the overall run partial and return a nonzero exit code; publish a complete export version only after coverage checks pass.
7. `--resume` continues only failed or unfinished tasks. Rerunning identical content must not create duplicate business records.
8. For ESR/PSD revisions across years, this phase prioritizes fully refreshing configured historical years for changed commodities; control costs with rate limits and resumable tasks.
9. Treat update endpoints, ETag, and Last-Modified as hints, with content hashes and business checks as the final evidence; an unchanged URL does not imply unchanged content.

Allow `as_of` queries only against actual release archives or captured snapshots. When retrieval occurs after the report date, retain both times separately; historical data backfilled from current interfaces must not be misrepresented as available at historical points in time.

**10. Error Handling and Run Logs**

- Use bounded exponential backoff for network timeouts, temporary 5xx responses, and 429 responses; honor `Retry-After`. Start with conservative concurrency and adjust based on observed rate limits.
- Report 401/403 authentication or access issues separately; do not retry indefinitely or pass HTML error pages to table parsers.
- When files are not found, distinguish "not yet released," "link changed," and "genuinely no data for that year." Do not treat every 404 as valid empty data.
- Validate response status, content type, file signatures, and JSON/ZIP parsability; bound ZIP member counts, uncompressed size, and extraction paths.
- On field changes or unknown layouts, stop publication of affected partitions, retain raw responses, and output a discrepancy list.
- Log source, task parameters, elapsed time, row counts, versions, retry counts, and error categories; redact API keys and authentication headers.
- Produce a machine-readable JSON summary and a short human-readable summary for each run.

**11. Verification Plan and Quality Gates**

Tests focus on risks that could cause missing data, incorrect values, or unrecoverable state, rather than duplicating tests for simple file wrappers.

| Verification category | Specific check | Pass criterion |
|---|---|---|
| Official spot checks | Sample values, units, years, and regions by source | Match official values from the same vintage; discrepancies have verifiable explanations |
| Primary keys | Complete business keys are unique within a snapshot | 0 unexplained duplicates |
| Dictionaries | Commodity, region, and measure codes have mappings | Unrecognized values enter an explicit exception list rather than being silently discarded |
| Coverage | Compare commodity/year/report-table coverage with the planned manifest | All required partitions succeed; genuine absence of data is supported by evidence |
| Nulls | Handle zero, blanks, suppressed values, and not-applicable cases separately | Missing values are not automatically filled with 0 |
| Units | Retain each source's units and scales | No direct summing or comparison across incompatible units |
| Revisions | Simulate changed values and deleted rows with old/new samples | The latest partition is correct and history remains traceable |
| Interruption recovery | Rerun after failures during download or output | No partially published files or duplicate records |
| Dates | Daylight saving time, year end, and marketing-year transitions | Release times are not confused with data periods |
| CSV round trip | Export and read back according to the schema | Leading zeros, numeric precision, dates, and nulls follow the contract |
| SQL usability | Verify representative tables and key constraints in a local temporary database | No nested objects or type conflicts; no connection to production databases |
| CLI/function consistency | Use both interfaces with the same configuration | Data match after normalizing sort order |

Apply supply/use balance tests only where documentation explicitly supports them for the same region, year, unit, and classification; account for residuals, rounding, and trade-year differences. RMA policy counts must not be added across overlapping coverage levels without verification.

**12. Phased Work Schedule**

These are estimates for one developer, excluding email-verification waits, official outages, and large-scale historical PDF extraction. Update estimates after sample validation. Every phase must produce runnable or inspectable outputs.

| Phase | Work | Outputs and exit conditions | Estimated effective workdays |
|---|---|---|---|
| A: Sources and samples | Obtain source samples, verify scope, request a key, and establish field mappings and release rules | Raw samples for every source; explicit unresolved issues and coverage boundaries | 1–2 |
| B: Foundation and WASDE | Project structure, HTTP/storage/state, historical CSVs, current files, and public functions/CLI | One end-to-end WASDE backfill and repeat-run verification completed | 2–3 |
| C: ERS | File discovery, series classification, long format, units, and historical definitions | Selected ERS files export consistently without mixing measurement bases | 1–2 |
| D: ESR | Authentication, dictionaries, annual tasks, weekly data, and revisions | Real requests pass; historical updates, year transitions, and negative-sales samples verified | 1–2 |
| E: PSD and monthly reports | Shared PSD downloads, three views, report archiving, and coverage checks | Numeric outputs, original reports, and coverage manifests for all three reports | 2–3 |
| F: RMA | Annual ZIPs, layouts, quantities/amounts, and complete dimensions | Multi-year downloads and validation pass; weekly update strategy is explicit | 1–2 |
| G: Backfill and delivery | Full-scope tasks, resume, CSV/SQL validation, documentation, and demonstrations | All acceptance items completed; gaps have explicit statuses | 2–3 |

Total: approximately **10–17 effective workdays**. If reports contain many key tables not covered by PSD, estimate additional extraction work separately; omitting those tables does not justify claiming completion.

Dependencies: begin B after sample confirmation in A; continue B, C, and F while waiting for the key; real API verification in D/E requires a valid key; G depends on completion of every source module. Validate small samples first, then expand historical scope.

**13. Final Delivery Checklist**

- [ ] Installable Python package and dependency configuration.
- [ ] 5 types of numeric-data downloaders, a shared monthly-report archiving module, and 7 dataset entry points.
- [ ] Python and CLI access for every dataset.
- [ ] Complete DataFrame/CSV outputs and coverage manifests for the default historical scope.
- [ ] Archives of raw files, raw responses, and report attachments.
- [ ] Field descriptions, types, units, null rules, and unique keys for every table.
- [ ] Documentation of economic meaning, time definitions, revisions, and historical vintages for each dataset.
- [ ] Official release rules, calendar sources, timezones, and scheduling instructions.
- [ ] Redacted configuration templates and API key setup instructions.
- [ ] Instructions for initial backfill, incremental updates, resume, and exception handling.
- [ ] Official spot-check results, key test results, CSV round trips, and local database-ingestion verification.
- [ ] README with complete steps from installation to downloading one example.
- [ ] Example notebook or short Python example showing function imports and DataFrame results.
- [ ] Table coverage manifests for the three FAS monthly reports, with uncovered items and reasons clearly visible.
- [ ] Known limitations, without describing unverified, failed, or partial work as complete.

**14. Defaults and Information Needed Before Development**

| Item | Current default | When additional information is needed |
|---|---|---|
| Nexus email and key | Do not invent an account; the intern applies using the company email | Before real ESR/PSD authentication integration tests |
| Historical span | From 2010 onward, with extension support | Change configuration if the supervisor requests a longer history |
| Commodity/region scope | All supported in-scope items; start integration with 3 commodities | Narrow configuration when explicit business constraints exist |
| Historical vintages | WASDE release archives + current historical values and subsequent snapshots for other sources | Separately assess archive extraction if complete historical point-in-time backtesting is required |
| Update timeliness | Support checks around releases; no second-level guarantee | Adjust scheduling and monitoring if the supervisor specifies latency targets |
| RMA product | State/County/Crop/Coverage Level SOB | Add separate sources if causes of loss or prevented planting are needed |
| SQL target | Typed CSV/schema outputs with local verification | Confirm PostgreSQL/MySQL or another target before production integration |

Implement Phases A and B first: establish the source inventory, obtain samples, and determine field mappings, then complete one end-to-end data pipeline with WASDE.

**15. Official Materials and Reference Index**

Access and verification date: 2026-11-12. In-text `[Sxx]` identifiers refer to the sources below. URLs are stored as code for easy copying and traceability when the Markdown file is viewed outside the chat interface.

- [S01] USDA: WASDE main page, release dates, current formats, and historical CSV update schedule. During this research, the official page was accessible through an official distribution domain.  
  `https://www.usda.gov/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report`  
  `https://usda.azureedge.us/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report`
- [S02] USDA NASS 2021 Spring Data Users’ Meeting: explains the difference between WASDE release history and PSD revised history. The explanation was read from the official document's search index during this research; direct access to the original PDF returned 404. Rediscover a working link from the official historical-data page during implementation.  
  `https://www.nass.usda.gov/Education_and_Outreach/Meeting/2021/2021-spring-questionandanswer.pdf`
- [S03] FAS Open Data portal: API key registration and access instructions.  
  `https://apps.fas.usda.gov/opendataweb/home`
- [S04] Official FAS Swagger: ESR/PSD paths, parameters, update endpoints, and the `X-Api-Key` definition. The API documentation does not fully enumerate response fields; verify the field contract using samples.  
  `https://apps.fas.usda.gov/opendatawebv2/assets/swagger/swagger.json`
- [S05] FAS Export Sales Reporting Program: weekly-report schedule and report definitions.  
  `https://fas-prod.azureedge.us/programs/export-sales-reporting-program`
- [S06] FAS report release calendar and World Agricultural Production release page: the 12:15 ET schedule for the three monthly reports.  
  `https://fas.usda.gov/`  
  `https://fas-prod.azureedge.us/report-release-announcement/world-agricultural-production-71`
- [S07] FAS World Agricultural Production report notes: relevant PSD updates at 12:00 and monthly report release at 12:15. The following report link is dynamic; save the actual retrieved version and hash during implementation.  
  `https://apps.fas.usda.gov/psdonline/circulars/production.pdf`
- [S08] ERS Commodity Costs and Returns product page: files, series, Last Updated, and Next Update.  
  `https://www.ers.usda.gov/data-products/commodity-costs-and-returns`
- [S09] ERS Commodity Costs and Returns Documentation: update patterns, estimation definitions, and historical methodologies.  
  `https://www.ers.usda.gov/data-products/commodity-costs-and-returns/documentation`
- [S10] RMA Summary of Business: states that the most recent five years update on Monday mornings.  
  `https://www.rma.usda.gov/summary-business`
- [S11] RMA State/County/Crop Summary of Business: annual ZIPs, delimiter format, and layout downloads.  
  `https://www.rma.usda.gov/tools-reports/summary-of-business/state-county-crop-summary-business`
- [S12] RMA Crop Insurance Experience with Coverage Level, 1989 Forward Record Layout, version dated 2026-05-28.  
  `https://pubfs-rma.fpac.usda.gov/pub/Web_Data_Files/Summary_of_Business/state_county_crop/SOB_State_County_Crop_with_Coverage_Level_1989_Forward.pdf`
- [S13] FAS Export Sales Query System user manual: report definitions, query methods, and marketing-year transitions.  
  `https://apps.fas.usda.gov/esrqs/assets/ESRQS_UserManual_PublicUser.pdf`
