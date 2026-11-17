# Costs and Returns (ERS): field guide

[Back to the field guide](../field_dictionary.md) · [Common conventions and nulls](common.md) · [Machine-readable field definitions](../../schemas/ers_costs_returns.v1.json)

## What this dataset describes

Describes costs, returns, and related production measures for an agricultural activity in a region and year. A row usually represents a specific item, such as seed costs per planted acre; it is neither an individual farm's bill nor the total expenditure of a region.

## How to read one row

In [costs-returns.csv](../../examples/costs-returns.csv), `Capital recovery of machinery and equipment` for corn in the Eastern Uplands in 2025 is `162.2 dollars per planted acre`. Read this as **$162.2 per planted acre**. `Base survey of 2021` identifies the underlying survey vintage; the data still describe 2025.

## Which columns to inspect first

Select `commodity`, `enterprise_type`, `region`, and `year` first, then `category` and `item`. Before comparing values, check that `unit`, `methodology`, `series_family`, and `forecast_vintage` are consistent.

The table below covers all 29 current fields. Values come from fixed repository examples and may be drawn from different records; do not combine the example-value column into a single record. Long JSON strings and identifiers are abbreviated with ellipses. The `schema.json` beside the export is authoritative for types, nullability, and the complete composite key.

## Business and verification fields

| CSV column | Meaning | Actual example value | Interpretation |
|---|---|---|---|
| `commodity` | Agricultural commodity | `Corn` | The commodity measured, such as Corn, Soybeans, or Milk. |
| `enterprise_type` | Production enterprise type | `Corn` | Distinguishes production stages/enterprise types for the same product. For crops, it usually matches commodity; for hogs and similar enterprises, retain original types such as farrowing and finishing rather than merging them into one pork-cost record. |
| `region` | Statistical region | `Eastern Uplands` | For example, Eastern Uplands is an ERS regional grouping, and U.S. total covers the entire United States. Region names do not necessarily correspond to states. |
| `country` | Country | `United States` | The country covered; these data currently mainly cover the United States. Read region and country together. |
| `size` | Enterprise size category | `No specific size` | Farm/enterprise size category in the original table. No specific size or not_specified means no size grouping was specified, not that size is zero. |
| `year_label` | Original year label | `2025` | Preserves the original text, such as 2025F, where F marks a forecast. It is not identical to the numeric year; do not discard the label and merge forecasts with estimates. |
| `series_family` | Source series | `Recent` | Recent is the recent series; Historical is the historical series; forecast denotes current forecasts; previously released forecasts denotes historical forecast releases. Categories may differ in methodology or vintage. |
| `methodology` | Survey basis/accounting methodology | `Base survey of 2021` | For example, Base survey of 2021 means the estimates are based on the 2021 base survey, not that this row describes 2021. It also distinguishes historical cash-cost, economic-cost, and other methodologies. |
| `table_title` | Original table title or format label | `machine readable` | Distinguishes source tables. machine readable identifies a machine-readable source table, not an economic measure. |
| `category` | Broad measure category | `Allocated overhead` | Examples include Operating costs, Allocated overhead, and Gross value of production. |
| `item` | Specific cost/return item | `Capital recovery of machinery and equipment` | Examples include capital recovery of machinery and equipment, hired labor, and seeds. Extra whitespace and some footnote markers have been removed; see source_item for the original text. |
| `unit` | Unit of the measure | `dollars per planted acre` | dollars per planted acre is a per-acre dollar amount; percent of acres is a percentage of acreage; planted acres is an acreage count. Not every row is in dollars. |
| `forecast_vintage` | Forecast release vintage | `not_applicable` / `Historical Forecast Zip Folder/cop_forecast_Dec 2025.xlsx` | Distinguishes forecasts made at different times for the same year. Historical forecasts usually retain the filename inside the ZIP; current_forecast denotes the current forecast, and non-forecasts use not_applicable. |
| `classification` | Additional source-table classification | `not_applicable` | Preserves column-level categories, such as tobacco types, so different types are not treated as one measure. Uses not_applicable when no such classification exists. |
| `year` | Year described by the measure | `2025` | Integer year parsed from year_label, such as 2025. It is neither the survey base year nor the download year. |
| `value` | Value of the cost/return measure | `162.2` | Interpret using this row's unit. For example, $162.2 per planted acre does not mean $162.2 of total regional spending. |
| `raw_value` | Original source value | `162.2` | Preserves the original numeric text or missing-value marker for checking value; use the parsed number for normal analysis. For historical Excel files, this is the stored value read by the reader, which may differ from the rounded value displayed in the interface. |
| `value_status` | Value status | `reported` | Indicates whether the value is reported normally, missing, not applicable, not reported, or another status. Check this column before handling nulls; only reported denotes a normally reported number, and zero can still be reported. |
| `estimate_status` | Estimate or forecast status | `unknown` | forecast means explicitly identified as a forecast; estimate means explicitly labeled as an estimate; unknown means the source file lacks sufficient labels. The current parser does not infer this from the year alone. |
| `source_item` | Original item name | `Capital recovery of machinery and equipment` | Original text before item cleanup, possibly including footnote markers and whitespace; used to check against the source. |
| `source_extra` | Other original fields | `{}` | JSON string preserving additional source-table codes, notes, and similar information. {} means no extra content. |
| `source_locator` | Original cell location | `{"record": 52}` | JSON string recording a CSV record number or Excel sheet, row, and column positions to locate the source. It is not a business category. |


## Time, provenance, and version fields

| CSV column | Meaning | Actual example value | Interpretation |
|---|---|---|---|
| `source_release_date` | Source release date | `2026-10-01` | The publication or update date explicitly provided by the source. It is neither the year described by the data nor the date you downloaded the file; see this page for its dataset-specific meaning. |
| `source_release_at_utc` | Source release timestamp (UTC) | `\N` | A complete, evidence-backed release timestamp normalized to UTC. Do not invent a time when only a date or month is known, or when the timezone is unavailable; this is usually stored as \N. |
| `release_time_precision` | Release time precision | `date` | How precisely the source release time is known: timestamp for an exact instant, date/day for a day, month for a month, and unknown when it cannot be established. This is not numeric decimal precision. |
| `retrieved_at_utc` | Local retrieval time (UTC) | `2026-11-17T12:57:06.299461+00:00` | When the source file associated with this snapshot was first retrieved or imported into the local cache. Offline fixture replay also generates a local import receipt; this timestamp cannot establish when the data first became public. |
| `source_artifact_id` | Raw file fingerprint | `a42362ce2c9b8f6a5992ae11ef6cb1ed12e25ec59b694782572daea646113951` | SHA-256 of the raw response, CSV, PDF, or ZIP, used to locate and verify the source file. It is not a commodity, region, or report-row identifier. |
| `snapshot_id` | Processed version identifier | `1283b9a74f19c7d6055eef45a024bc5b0b4a53dbac0cd7d7962b936842e851e2` | Identifies a normalized version produced from the source file together with the parser, field definitions, and configuration. Reprocessing the same source may produce a new version; do not treat it as economic time or a business key. |
| `vintage_type` | Data vintage type | `current_revised` | report_vintage preserves values as published in a specific report; current_revised is the historical series available at download time, possibly revised; forecast_vintage preserves a specific forecast release. |

## Common pitfalls

- `year=2025` does not guarantee a single value: different forecast vintages, survey methodologies, and enterprise types may coexist.
- Costs per acre, per head of cattle, and per hundredweight cannot be added directly. Item subtotals must not be added again to their components.
- In specific supported historical tables, source footnote `1/` means "included elsewhere" and is parsed as `included_elsewhere`, not zero cost.
- `source_release_date` is usually the file update date provided by the source page, not automatically the exact original publication date of a historical forecast file; use `forecast_vintage` first to identify forecast versions.

For more source and processing details, see the [Costs and Returns technical guide](../costs_returns.md).
