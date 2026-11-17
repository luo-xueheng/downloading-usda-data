# Source registry

Access checked: 2026-11-12 (Asia/Shanghai). Exact UTC acquisition timestamps, response codes, final URLs and SHA-256 values are saved beside each raw response. Machine-readable registry: `config/source_registry.json`. Frozen file inventory: `config/expected_coverage.json`.

## Discovery and access

### wasde

- Official landing: `https://www.usda.gov/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report`
- Landing response: 200. Raw evidence: `artifacts/acceptance/phase-00/discovery/wasde.html`.
- Discovery: Follow landing-page current XML/XLS/PDF/TXT links and historical-page CSV/ZIP links. Canonical history page returned 403; saved USDA distribution copy supplies the file links.
- Verified discovery response: `artifacts/acceptance/phase-00/discovery/wasde.html` (`https://www.usda.gov/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report`).
- Authentication: Public; no authentication.
- Formats: CSV, XML, XLS, PDF, TXT, historical ZIP.
- Coverage: Report-date vintages; structured archive begins April 2010 at file level. Per-table coverage deferred to Phase 02.
- Access limitation: None for the saved public discovery response.

### fas-esr

- Official landing: `https://www.fas.usda.gov/programs/export-sales-reporting-program`
- Landing response: 403. Raw evidence: `artifacts/acceptance/phase-00/discovery/esr.html`.
- Discovery: Use ESR program page, linked ESRQS portal and official Open Data Swagger. Expand commodity, country, region and unit dictionaries in Phase 04.
- Verified discovery response: `artifacts/acceptance/phase-00/discovery/esr-program-cdn.html` (`https://fas-prod.azureedge.us/programs/export-sales-reporting-program`).
- Authentication: api.data.gov key in X-Api-Key for Open Data; public program documentation.
- Formats: API JSON; response shape unverified.
- Coverage: Source marketing years; exact per-series historical coverage unverified until authenticated discovery.
- Access limitation: Canonical landing HTTP 403; public alternate discovery and fixtures succeeded. Not a permanent source-unavailability claim.

### fas-psd

- Official landing: `https://apps.fas.usda.gov/opendataweb/home`
- Landing response: 200. Raw evidence: `artifacts/acceptance/phase-00/discovery/api-portal.html`.
- Discovery: Portal redirects to opendatawebv2; inspect its official Swagger. Expand dictionaries only into the three report families in Phase 05.
- Verified discovery response: `artifacts/acceptance/phase-00/discovery/swagger.json` (`https://apps.fas.usda.gov/opendatawebv2/assets/swagger/swagger.json`).
- Authentication: api.data.gov key in X-Api-Key for Open Data; PSD public report directory requires none.
- Formats: API JSON; public PDF reports and JSON discovery metadata.
- Coverage: Current revised observations; no promise of past monthly API vintages. Per-series dates deferred to Phase 05.
- Access limitation: None for the saved public discovery response.

### ers-costs-returns

- Official landing: `https://www.ers.usda.gov/data-products/commodity-costs-and-returns`
- Landing response: 200. Raw evidence: `artifacts/acceptance/phase-00/discovery/ers.html`.
- Discovery: Enumerate every download in Recent, Historical, current forecasts and previously released forecast ZIP. Preserve section, enterprise, dates and format.
- Verified discovery response: `artifacts/acceptance/phase-00/discovery/ers.html` (`https://www.ers.usda.gov/data-products/commodity-costs-and-returns`).
- Authentication: Public; no authentication.
- Formats: CSV, XLSX, historical XLS, ZIP.
- Coverage: Observation years; coverage varies by commodity/enterprise/method; Historical discontinued commodities retained in inventory.
- Access limitation: None for the saved public discovery response.

### rma-sob

- Official landing: `https://www.rma.usda.gov/tools-reports/summary-of-business/state-county-crop-summary-business`
- Landing response: 200. Raw evidence: `artifacts/acceptance/phase-00/discovery/rma.html`.
- Discovery: Follow State/County/Crop/Coverage Level 1989-present annual ZIP and layout links; separately inventory earlier layout; exclude Type/Practice/Unit.
- Verified discovery response: `artifacts/acceptance/phase-00/discovery/rma.html` (`https://www.rma.usda.gov/tools-reports/summary-of-business/state-county-crop-summary-business`).
- Authentication: Public; no authentication.
- Formats: ZIP with pipe-delimited text; PDF/DOC layouts.
- Coverage: Commodity years 1989-2027 currently listed for coverage-level product; 1948-1988 is a distinct unsupported earlier layout, not silently included.
- Access limitation: None for the saved public discovery response.

### world-production

- Official landing: `https://www.fas.usda.gov/data/world-agricultural-production`
- Landing response: 403. Raw evidence: `artifacts/acceptance/phase-00/discovery/wap.html`.
- Discovery: Use PSD Online application CircularsHandler plus circularSettings URL construction and production family code; verify PDF identity. Original FAS landing currently returns 403.
- Verified discovery response: `artifacts/acceptance/phase-00/discovery/fas-circular-inventory.json` (`https://apps.fas.usda.gov/psdonline/CircularsHandler.ashx`).
- Authentication: Public; no authentication.
- Formats: PDF; public directory JSON.
- Coverage: Global report directory months are candidates, not proof each family attachment exists.
- Access limitation: Canonical landing HTTP 403; public alternate discovery and fixtures succeeded. Not a permanent source-unavailability claim.

### grain-trade

- Official landing: `https://www.fas.usda.gov/data/grain-world-markets-and-trade`
- Landing response: 403. Raw evidence: `artifacts/acceptance/phase-00/discovery/grain.html`.
- Discovery: Use PSD Online application CircularsHandler plus circularSettings URL construction and Grain family code; verify PDF identity. Original FAS landing currently returns 403.
- Verified discovery response: `artifacts/acceptance/phase-00/discovery/fas-circular-inventory.json` (`https://apps.fas.usda.gov/psdonline/CircularsHandler.ashx`).
- Authentication: Public; no authentication.
- Formats: PDF; public directory JSON.
- Coverage: Global report directory months are candidates; retain marketing-year versus trade-year distinctions.
- Access limitation: Canonical landing HTTP 403; public alternate discovery and fixtures succeeded. Not a permanent source-unavailability claim.

### oilseed-trade

- Official landing: `https://www.fas.usda.gov/data/oilseeds-world-markets-and-trade`
- Landing response: 403. Raw evidence: `artifacts/acceptance/phase-00/discovery/oilseed.html`.
- Discovery: Use PSD Online application CircularsHandler plus circularSettings URL construction and Oilseeds family code; verify PDF identity. Original FAS landing currently returns 403.
- Verified discovery response: `artifacts/acceptance/phase-00/discovery/fas-circular-inventory.json` (`https://apps.fas.usda.gov/psdonline/CircularsHandler.ashx`).
- Authentication: Public; no authentication.
- Formats: PDF; public directory JSON.
- Coverage: Only oilseed, meal and oil report-family scope; other PSD circulars excluded.
- Access limitation: Canonical landing HTTP 403; public alternate discovery and fixtures succeeded. Not a permanent source-unavailability claim.

## Publication records

Timezone `unknown` must stay unknown. Retrieval time and HTTP Last-Modified do not establish publication time. Precision describes the official claim, not measured service availability. Dates listed as Next Update are plans.

| ID / kind | Claim | Precision / timezone | Status | Official locator and local evidence |
|---|---|---|---|---|
| wasde-report / report | Monthly on published annual calendar, 12:00 PM ET. November 2026 release is November 10; October release is October 9.  | minute / America/New_York | verified | 2026 WASDE Release Dates (12:00pm ET); November 2026 WASDE Report in `artifacts/acceptance/phase-00/discovery/wasde.html` |
| wasde-history / historical_csv | Historical CSV updated the day after the WASDE release; exact time is not specified. HTTP Last-Modified is not the publication timestamp; file creation metadata can predate documented availability. | day / unknown | verified | Consolidated Historical WASDE Report Data in `artifacts/acceptance/phase-00/discovery/wasde.html` |
| esr-weekly / weekly_report | Weekly summary Thursday 8:30 a.m. ET unless changed; preceding Friday/Monday national holiday moves the summary to Friday. Reporting week is Friday through Thursday.  | minute / America/New_York | verified | Weekly Reporting in `artifacts/acceptance/phase-00/discovery/esr-program-cdn.html` |
| esr-api / api | Actual API availability relative to weekly report release has not been measured. Phase 04 must check datareleasedates and real authorized responses; do not assume simultaneous availability. | unknown / unknown | unverified | No verified official availability evidence; explicitly deferred |
| world-production-report / report | Monthly circular release convention: by 12:15 p.m. after the same-day 12:00 p.m. PSD update. Clock convention appears in report notes; timezone for that sentence is not explicit. Eastern timezone appears in WAP next-release notice. Scheduling reconciliation remains deferred; do not manufacture a timestamp. | minute / unknown | verified | November 2026 WAP PDF page 17, publication availability paragraph (12:00 PSD and by 12:15 circular) in `tests/fixtures/raw/world-production-development.pdf` |
| grain-trade-report / report | Monthly circular release convention: by 12:15 p.m. after the same-day 12:00 p.m. PSD update. Clock convention appears in report notes; timezone for that sentence is not explicit. Eastern timezone appears in WAP next-release notice. Scheduling reconciliation remains deferred; do not manufacture a timestamp. | minute / unknown | verified | November 2026 Grain PDF page 3, publication availability paragraph in `tests/fixtures/raw/grain-trade-development.pdf` |
| oilseed-trade-report / report | Monthly circular release convention: by 12:15 p.m. after the same-day 12:00 p.m. PSD update. Clock convention appears in report notes; timezone for that sentence is not explicit. Eastern timezone appears in WAP next-release notice. Scheduling reconciliation remains deferred; do not manufacture a timestamp. | minute / unknown | verified | November 2026 Oilseeds PDF page 8, publication availability paragraph in `tests/fixtures/raw/oilseed-trade-development.pdf` |
| psd-api-convention / api | Report notes state cotton, oilseed and grain PSD data update at 12:00 p.m. on WASDE release days; this is a documented convention, not an authenticated availability measurement. Phase 05/08 must verify actual API timestamps and timezone before scheduling. | minute / unknown | verified | November 2026 WAP PDF page 17, publication availability paragraph (12:00 PSD and by 12:15 circular) in `tests/fixtures/raw/world-production-development.pdf` |
| psd-directory-schedule / public_schedule_metadata | Public PSD schedule currently lists December 10, 2026 at 12:00PM for grains, oilseeds and WAP. Potential distinction between PSD update and report deadline: retain the raw record; do not overwrite the report by-12:15 convention. | minute / unknown | verified | releaseDate, releaseTime and releaseDescription of the three in-scope families in `artifacts/acceptance/phase-00/discovery/psd-schedule.json` |
| ers-estimates / annual_estimate | Preliminary annual estimates during first week of May; final estimates during first week of October.  | week / unknown | verified | Overview and Scope/Coverage of Data in `artifacts/acceptance/phase-00/discovery/ers-methodology.html` |
| ers-forecasts / forecast | Cost-of-production forecasts generally updated in mid-June and mid-November.  | part_of_month / unknown | verified | Overview; Cost of Production Forecasts in `artifacts/acceptance/phase-00/discovery/ers-methodology.html` |
| ers-file-dates / file_metadata | Recent files: Last Updated 2026-10-01, Next Update 2027-05-03. Forecast files: Last Updated 2026-11-10, Next Update 2027-06-17. Next Update is a planned date, not proof of future release. No precise release time is provided. | day / unknown | verified | File Downloads; per-file time elements in `artifacts/acceptance/phase-00/discovery/ers.html` |
| rma-summary-refresh / summary_report | Most recent five years refreshed each Monday morning, covering data accepted through preceding week; older report years no longer updated. Official page does not specify timezone or minute. Observed ZIP Last-Modified is separate transport metadata. | part_of_day / unknown | verified | Summary of Business description in `artifacts/acceptance/phase-00/discovery/rma-summary.html` |
| rma-zip-refresh / annual_zip | Annual bulk ZIP synchronization with the Monday summary-report refresh is not independently established. Must be verified in Phase 07/08; do not apply summary-report rule to ZIP files as an established fact. | unknown / unknown | unverified | No verified official availability evidence; explicitly deferred |

## API contract and expansion

`swagger.json` is an official specification, not evidence that a live authenticated request works. Its `securityDefinitions.apiKeyHeader` specifies `X-Api-Key` in the request header. The portal JavaScript instructs users to obtain an api.data.gov key. The API host root returned HTTP 404; this is preserved and is not listed as a verified data endpoint. No credential was present and no authenticated API response was claimed.

Phase 04 expands ESR commodities, countries, regions, units and release dates using the documented paths in `scope.json`. Phase 05 expands PSD dictionaries and discovers marketing years for the three report families only. All dictionary codes and response field contracts remain deferred. Freeze the expanded inventory before the relevant adapter tests; unresolved required report mappings must remain visible through Phase 06.

## Inventory and access limitations

- The saved pages yield 80 WASDE links, 73 ERS links, 44 RMA links (including layout documents and the separately identified older layout), and 243 directory months for each of the three FAS report families. A listed link is not a successful download. Fourteen saved fixtures are individually verified.
- WASDE consolidated downloads begin at the file-level boundary April 2010. Do not infer all tables or series begin then. The raw archive advertises earlier reports, but earlier structured layout support is not established.
- ERS inventory retains Recent, Historical, current forecasts and previously released forecasts, every listed enterprise, and discontinued products such as sugar beets and tobacco. Apply the 2010 year filter later; do not erase historical files from discovery.
- RMA coverage-level ZIP links range from commodity year 1989 to 2027. Commodity year 2027 being listed during 2026 is valid source labeling. The distinct 1948-1988 layout is explicitly outside currently supported layouts; no layout is implemented in Phase 00.
- October 2025 is absent from the saved WASDE CSV links and global FAS report-month directory. This is an unresolved directory gap, not evidence of permanent unavailability. Later phases must investigate official announcements and archives.
- Canonical FAS report/program pages and canonical WASDE history paths returned 403 in this environment. Successful public PSD discovery and downloaded report bytes satisfy public-source discovery. USDA/FAS distribution copies are retained as alternate evidence; the original responses remain visible.
- FAS distribution grain/oilseed URLs redirect to a common search page and return identical bytes; these are not treated as verified family-filtered lists. The official PSD directory, application URL template and the downloaded PDF identity establish the report acquisition chain.
- Public PSD schedule metadata says 12:00PM, while circulars state by 12:15PM. Keep API/data update and report availability separate. Phase 08 must reconcile the intended event and timezone before scheduling.
- Historical monthly API vintages are not inferred from today's revised historical observations. No API-to-report numeric equality is asserted in Phase 00.

## Phase 04 authenticated ESR verification (2026-11-15)

All five ESR dictionary/release endpoints and real commodity/year and destination endpoints returned HTTP 200 JSON with the user-supplied key. See config/esr_inventory.json and artifacts/acceptance/phase-04/live/authenticated_checks.json for exact URL/hash/count evidence. Response market-year semantics and boundary-week behavior are documented in docs/export_sales.md. PSD authenticated verification remains pending Phase 05. Earlier Phase 00 access statements remain historical acquisition records.

## Phase 05 authenticated PSD verification (2026-11-15)

PSD dictionary, country/year, individual-country, world and commodity release-inventory requests returned HTTP 200 JSON. Scope remains the 37-code union of the three requested report families. Exact source fields, source month precision, world code 00, nullable region dictionary reference R15, and current-revised provenance are documented in docs/psd.md. See config/psd_scope.json and artifacts/acceptance/phase-05/live/checks.json. Supplementary report coverage is not yet accepted; it belongs to Phase 06.

## Phase 10 handover reconciliation (2026-11-17 Asia/Shanghai)

The preceding Phase 00/04/05 paragraphs are historical acquisition records, not
current unresolved implementation claims. All seven source adapters and the full
Phase 09 backfill passed their gates. The frozen inventory and initial claims in
config/source_registry.json remain unchanged for reproducibility. Final coverage
is in artifacts/acceptance/phase-09/coverage_manifest.csv, with 1,417 expected
records = 1,404 succeeded + 13 evidenced source-unavailable and zero unresolved.
The October 2025 investigation and June 2016 WAP Table 10 omission have explicit
source evidence there. The API-to-report and bulk-ZIP synchronization claims are
still unmeasured; successful authenticated access does not establish them.

The handover release notes and calendar preserve source-specific time precision.
Future release events remain plans. Phase 10 reruns bounded official checks and
records their actual status separately; it does not move the full-run cutoff.

Phase 10 recheck note: the pinned RMA 2010 ZIP URL currently returns HTTP 502 via
both environment-proxy and explicit direct requests. This blocks the final live
holdout recheck. It does not erase the pinned historical artifact or establish
permanent source unavailability. See artifacts/acceptance/phase-10/phase-00-direct/
and rma-direct-diagnostic.json.
