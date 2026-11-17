# WASDE: field guide

[Back to the field guide](../field_dictionary.md) · [Common conventions and nulls](common.md) · [Machine-readable field definitions](../../schemas/wasde_observations.v2.json)

## What this dataset describes

WASDE is a periodically released report of agricultural supply and demand estimates. The CSV usually expands each numeric cell in an original table into one row: the value a specific release gives for a region, commodity, marketing year, and attribute. It also includes price and forecast-reliability tables, so not every `Value` represents production.

## How to read one row

In [wasde.csv](../../examples/wasde.csv), report number 677, released on 2026-11-10, lists `Beginning Stocks` of `1123.00` for Mexican sugar in marketing year 2025/26, in thousand metric tons (actual weight). Read this as **beginning stocks of 1.123 million metric tons**, not 1123 tons; `Est.` indicates an estimate.

## Which columns to inspect first

Filter by `ReportTitle`, `Commodity`, `Region`, `MarketYear`, and `Attribute` first, then examine `Value` and `Unit`. When comparing forecasts across releases, also retain `source_release_date`; do not deduplicate solely by marketing year.

The table below covers all 30 current fields. Values come from fixed repository examples and may be drawn from different records; do not combine the example-value column into a single record. Long JSON strings and identifiers are abbreviated with ellipses. The `schema.json` beside the export is authoritative for types, nullability, and the complete composite key.

## Business and verification fields

| CSV column | Meaning | Actual example value | Interpretation |
|---|---|---|---|
| `WasdeNumber` | Report issue number | `677` | USDA's number for this WASDE issue. 677 means the 677th issue, not a year. |
| `ReportDate` | Report month label | `November 2026` | The original report's month text, such as November 2026. It identifies the report issue; see ReleaseDate for the exact publication date. |
| `ReportTitle` | Original table title | `Mexico Sugar Supply and Use and High Fructose Corn Syrup Consumption` | Identifies the report table containing this row. The same commodity may appear in supply/use, price, and forecast-reliability tables, so interpret it together with the title. |
| `Attribute` | Statistical measure | `Beginning Stocks` | What this row measures, such as Beginning Stocks, Production, or Ending Stocks. The measure cannot be determined from Value alone. |
| `ReliabilityProjection` | Forecast-reliability statistic category | `not_applicable` / `above_final` | Used only in reliability/error tables, such as average (average difference statistics) or above_final (the category for years when the projection exceeded the final result). Other tables use not_applicable. Interpret it with the original table and Unit; do not treat error statistics as production. |
| `Commodity` | Commodity or product category | `Sugar` | The commodity measured in the original table, such as Sugar or Corn. Original varieties/subcategories are preserved rather than collapsed into broad categories. |
| `Region` | Statistical region or aggregate scope | `Mexico` | Examples include Mexico, United States, and World. It can also be an aggregate group; do not assume every name represents an individual country. |
| `MarketYear` | Marketing year described by the data | `2025/26` | For example, 2025/26 follows the commodity's marketing year, not the report publication year. It is not_applicable when there is no single year, as in some reliability tables. |
| `ProjEstFlag` | Estimate/projection flag | `Est.` | Est. means estimated, Proj. means projected, and not_labelled means the original table did not label it. Do not assume a value is final merely because its year has passed. |
| `AnnualQuarterFlag` | Annual/quarterly basis | `Annual` | The annual or quarterly statistical label supplied by the original table. Annual denotes a full year; quarterly and full-year records must not be summed together. |
| `Value` | Value of the measure | `1123.00` | Use with Attribute, Commodity, Region, MarketYear, and Unit. The number itself does not contain a unit and has not been universally converted to tons. |
| `Unit` | Unit and scale | `1000 Metric Tons, Actual Weight` | For example, 1000 Metric Tons, Actual Weight means thousand metric tons on an actual-weight basis; 1123.00 represents 1,123,000 metric tons. Other tables may contain prices, numbers of years, or percentages. |
| `ReleaseDate` | Original release date text | `2026-11-10` | The release date in the source CSV, such as 2026-11-10. source_release_date is parsed from it; neither field is MarketYear. |
| `ReleaseTime` | Original release clock time | `12:00:00.0000000` | Time text retained from the source CSV. Without independently confirmed timezone information, it is neither treated directly as UTC nor used to populate source_release_at_utc. |
| `ForecastYear` | Forecast/report batch year | `2026` | The year identifying this forecast batch in the source CSV; do not treat it as the marketing year of the value, which is given by MarketYear. |
| `ForecastMonth` | Forecast/report batch month | `11` | The month identifying this forecast batch in the source CSV; 11 means November. Together with ForecastYear it identifies the batch, not the crop harvest month. |
| `raw_value` | Original source value | `1123.00` | Preserves the original numeric text or missing-value marker for checking value; use the parsed number for normal analysis. For historical Excel files, this is the stored value read by the reader, which may differ from the rounded value displayed in the interface. |
| `value_status` | Value status | `reported` | Indicates whether the value is reported normally, missing, not applicable, not reported, or another status. Check this column before handling nulls; only reported denotes a normally reported number, and zero can still be reported. |
| `raw_optional_dimensions` | Original optional classifications | `{"MarketYear": "2025/26", "ProjEstFlag": "Est.", "ReliabilityProj…` | JSON string retaining original blanks or labels for MarketYear, ProjEstFlag, and ReliabilityProjection. Useful for checking how values such as not_applicable were assigned. |
| `source_member` | Filename inside the ZIP | Empty string | Records the internal CSV filename when the source is a ZIP; usually an empty string for directly downloaded standalone CSVs. |
| `source_dimension_repair` | Dimension repair evidence identifier | Empty string | Populated only for a specific, verified source-file defect. An empty string means no repair was applied; this is not a record of automatic numeric changes. |
| `source_original_dimensions` | Field contents before repair | `{}` | JSON string recording original contents before a dimension repair. {} means there are no repair details to record. |
| `source_conflict` | Known cross-format discrepancy | Empty string | Records known numeric discrepancies between CSV/XML and PDF at the same location, with supporting evidence. An empty string means none is recorded; for registered discrepancies, CSV values still follow the selected structured source. |


## Time, provenance, and version fields

| CSV column | Meaning | Actual example value | Interpretation |
|---|---|---|---|
| `source_release_date` | Source release date | `2026-11-10` | The publication or update date explicitly provided by the source. It is neither the year described by the data nor the date you downloaded the file; see this page for its dataset-specific meaning. |
| `source_release_at_utc` | Source release timestamp (UTC) | `\N` | A complete, evidence-backed release timestamp normalized to UTC. Do not invent a time when only a date or month is known, or when the timezone is unavailable; this is usually stored as \N. |
| `release_time_precision` | Release time precision | `date` | How precisely the source release time is known: timestamp for an exact instant, date/day for a day, month for a month, and unknown when it cannot be established. This is not numeric decimal precision. |
| `retrieved_at_utc` | Local retrieval time (UTC) | `2026-11-17T12:57:06.172384+00:00` | When the source file associated with this snapshot was first retrieved or imported into the local cache. Offline fixture replay also generates a local import receipt; this timestamp cannot establish when the data first became public. |
| `source_artifact_id` | Raw file fingerprint | `1a28972ac0c727ce974e0f8217b3cae9e892f6e974f6927033eaffbd5890a8da` | SHA-256 of the raw response, CSV, PDF, or ZIP, used to locate and verify the source file. It is not a commodity, region, or report-row identifier. |
| `snapshot_id` | Processed version identifier | `483832b47869d6dc7582393dcd5cd4e329c25a574629f91185ee9c242d933327` | Identifies a normalized version produced from the source file together with the parser, field definitions, and configuration. Reprocessing the same source may produce a new version; do not treat it as economic time or a business key. |
| `vintage_type` | Data vintage type | `report_vintage` | report_vintage preserves values as published in a specific report; current_revised is the historical series available at download time, possibly revised; forecast_vintage preserves a specific forecast release. |

## Common pitfalls

- The same marketing year can appear in multiple reports; these are different release vintages, not duplicate rows caused by repeated downloads.
- `Beginning Stocks` and `Ending Stocks` are stocks; `Production` and `Exports` measure flows over a period. Errors and counts of years in forecast-reliability tables must not be added to supply/use quantities.
- This interface determines the release date from `ReleaseDate`; the UTC release timestamp remains null when there is insufficient timezone evidence for the source clock time.

For more source and processing details, see the [WASDE technical guide](../wasde.md).
