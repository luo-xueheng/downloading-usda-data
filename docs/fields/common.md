# Read this first: values, units, years, and provenance

[Back to the field guide](../field_dictionary.md)

## A row is not necessarily a transaction

| Dataset | What one row represents |
|---|---|
| WASDE | One numeric cell for a commodity, region, period, and attribute in a specific report release |
| Costs and Returns | One cost, return, or production measure for an enterprise type, region, year, and methodology |
| Export Sales | A set of sales/shipment measures for a commodity, destination, marketing year, and reporting week |
| World Agricultural Production / Grain Trade / Oilseed Trade | One PSD measure or one original report-table cell; distinguish them first using observation_kind |
| RMA | A business summary for a combination of state/county, crop, year, insurance plan, and coverage conditions, not an individual policy |

The code identifies duplicate rows using a "composite key" made up of multiple business fields. Deduplicating by only "commodity + year," for example, would incorrectly remove records for different regions, measures, report vintages, or insurance conditions. Exact key fields are marked with `key: true` in the `schema.json` accompanying each CSV.

## What blanks, zeros, and special labels mean

| What you see | Interpretation | What to avoid |
|---|---|---|
| `\N` | A true null in the CSV encoding; it may result from unknown or unavailable source information | Do not automatically replace it with 0 |
| `0`, `0.00` | A meaningful zero, still subject to the status and source context | Do not treat it as missing |
| Empty string | A text field has no content, such as a standalone CSV with no ZIP member filename | Do not assume it is equivalent to `\N` |
| `not_applicable` | This classification does not apply to the row, such as an API record with no PDF report issue | Do not fill it with a guessed year/category |
| `unknown` | There is insufficient information, such as whether a value is estimated or final | Do not treat it as confirmed final data |
| `not_labelled`, `not_specified` | The source file did not label/specify this classification | Do not interpret it as a numeric zero |
| `reported` | A normally reported value status | Do not automatically interpret it as finalized |
| `missing` | The original number is missing or blank | Do not automatically fill it with zero |
| `unavailable`, `not_reported` | The source did not provide/publish this value | Do not interpret it as no actual production/transactions |
| `suppressed` | The source replaced the number with a withholding/suppression marker | Do not guess the hidden value |
| `included_elsewhere` | This item is included in another item; see the relevant table footnotes | Do not count it again in total costs or assume it is zero |

Not every dataset uses every status. WASDE, ERS, and report tables use `value_status` to explain absent numbers; original Export Sales nulls are retained in `raw_metrics`, while RMA also requires checking `missing_fields` and `count_availability`.

Actual text beginning with a backslash is escaped, so the literal text `\N` can be distinguished from a true null. For lossless reading, use the provided `Schema.read_csv` or `Schema.read_csv_chunks` rather than automatic type inference in spreadsheet software.

## Check units before interpreting magnitude

| Unit notation | Meaning | Reading example |
|---|---|---|
| `Metric Tons`, `MT` | Metric tons | 100 means 100 metric tons |
| `(1000 MT)`, `Thousand Metric Tons` | Thousand metric tons | 100 means 100,000 metric tons |
| `Million Metric Tons` | Million metric tons | 100 means 100 million metric tons |
| `(1000 HA)` | Thousand hectares | 100 means 100,000 hectares |
| `Million Hectares` | Million hectares | Interpret the area with a multiplier of one million |
| `(MT/HA)` | Metric tons per hectare, i.e. yield | 6.2148 means 6.2148 metric tons per hectare |
| `dollars per planted acre` | Dollars per planted acre | 162.2 means $162.2 per planted acre, not total spending |
| `Percent` | Percentage | 2.5 means 2.5%, not 250% |
| RMA `coverage_level` | Proportion | 0.5000 means 50% |
| RMA `loss_ratio` | Indemnities-to-premiums ratio | 1.50 means 1.5 times, or 150% |

These are examples of how to read common units, not a unified unit dictionary for all sources. Cotton, livestock products, and price tables may use other units, such as bales, pounds, pieces, or amounts per hundredweight. Do not change a unit label without converting its value, or directly sum rows with different units.

## Keep four kinds of time separate

| Time concept | Common fields | Question answered |
|---|---|---|
| Period described by the data | `MarketYear`, `marketYear`, `period_label`, `year`, `commodity_year` | When does this production/cost/insurance activity belong? |
| Report or forecast vintage | `report_period`, `ReleaseDate`, `forecast_vintage` | Which release of the estimate am I looking at? |
| Source record update information | `calendarYear`, `source_calendar_year`, `month`, `source_month` | In which month does the API say this record was updated? |
| Local retrieval/import time | `retrieved_at_utc` | When did this file enter the current cache? |

Marketing-year boundaries vary by source, commodity, region, or measure. Do not simplify `2025/26` to "calendar year 2025" or assume that identical year identifiers in ESR and PSD necessarily refer to exactly the same period.

## What vintage_type means

- **`report_vintage`: original report vintage.** For example, a November report's forecast for the following year retains the value known that November.
- **`current_revised`: current revised vintage.** A value for a historical year returned by the API today may have been revised and may differ from its first publication.
- **`forecast_vintage`: a specific forecast release.** The same target year can have different forecasts issued in June, December, and other months; do not deduplicate using only the target year.

For example, different values for "2025/26 production" across releases do not necessarily indicate a code error. Make clear whether you are comparing different forecasts for the same year or different years within one release vintage.

## Why provenance fields are so long

`source_artifact_id` is the raw file fingerprint, and `snapshot_id` is the processed version identifier. They are generally not filtering dimensions for business-trend analysis, but are useful for checking sources, distinguishing revisions, and investigating discrepancies. They cannot replace commodity, region, measure, and period.

JSON strings in cells, such as `source_locations`, `source_extra`, and `raw_metrics`, package additional information into one CSV cell; they are not another data table that must be expanded horizontally, nor do they represent multiple business amounts.
