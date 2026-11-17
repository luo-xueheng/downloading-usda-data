# Standalone auxiliary PSD interface: field guide

[Back to the field guide](../field_dictionary.md) · [Common conventions and nulls](common.md) · [Machine-readable field definitions](../../schemas/psd_observations.v1.json)

## What this dataset describes

PSD is the Production, Supply and Distribution database, providing measures such as production, area, consumption, trade, and stocks for a commodity, region, and marketing year. Each row corresponds to one supply/use measure. It is also the shared source for the three report datasets and does not add another primary-dataset example CSV.

## How to read one row

`commodityCode=0440000` identifies corn; a row's region, `marketYear`, `attribute_name`, and `unit` together determine whether `value` represents production, area, or another measure. `calendarYear` and `month` identify the source record's update year and month, not the year to which the production belongs.

## Which columns to inspect first

Start with `commodity_name`, `geography_name`, `marketYear`, `attribute_name`, `value`, and `unit`; check `aggregation_level` before comparing, and do not add regional totals to their member countries.

The table below covers all 27 current fields. Values come from fixed repository examples and may be drawn from different records; do not combine the example-value column into a single record. Long JSON strings and identifiers are abbreviated with ellipses. The `schema.json` beside the export is authoritative for types, nullability, and the complete composite key.

## Business and verification fields

| CSV column | Meaning | Actual example value | Interpretation |
|---|---|---|---|
| `commodityCode` | PSD commodity code | `0440000` | The supply/use database's own commodity code; 0440000 means corn. Preserve leading zeros and do not join directly to ESR/RMA commodity codes. |
| `countryCode` | PSD country/aggregate code | `AF` | Country, region, or other aggregate code; 00 is the world total. Use with aggregation_level; do not treat every code as an individual country. |
| `aggregation_level` | Geographic aggregation level | `country` | For PSD, this can be country, region (regional total), world, or residual_aggregate (other/residual total); PDF rows use report_defined and must be interpreted from the original table. |
| `marketYear` | Marketing-year identifier | `2025` | The source API's marketing-year identifier. Exact boundaries vary by commodity, region, and measure; it is not assumed to be a calendar year or directly equivalent to the ESR parameter with the same name. |
| `attributeId` | Measure code | `4` | Measure identifier in the source dictionary; use with attribute_name. |
| `unitId` | Unit code | `4` | Source unit identifier; use with unit. Units may differ by commodity or measure. |
| `calendarYear` | Source record update year | `2026` | Year of the record's update batch, not the marketing year; it also does not prove that the same historical report value was available in that year. |
| `month` | Source record update month | `09` | Month of the record's update batch, retaining the source string; together with calendarYear, it expresses the update year and month. |
| `commodity_name` | Commodity name | `Corn` | Official commodity/product name corresponding to the code, such as Corn. |
| `geography_name` | Geographic name | `Afghanistan` | Official name of a country or aggregate region; the world total is not calculated by the program by summing countries. |
| `region_code` | Parent region code | `R12` | Regional membership from the country dictionary; it does not create an additional regional total. |
| `region_name` | Parent region name | `South Asia` | Name looked up in the region dictionary. If the source country dictionary refers to a region absent from the region dictionary, this stays null; no name is invented. |
| `region_mapping_status` | Region-name lookup status | `resolved` | resolved means a successful match; absent_in_source_dictionary means the corresponding region is missing from the source dictionary. The original region_code is still retained. |
| `genc_code` | GENC geographic code | `AFG` | Geographic identifier supplied by the source dictionary, such as MEX. If absent, it is \N; do not fill it arbitrarily using another coding system. |
| `attribute_name` | Supply/use measure name | `Area Harvested` | Examples include Production, Area Harvested, and TY Exports (trade-year exports). MY and TY measures are not interchangeable. |
| `unit` | Cleaned unit name | `(1000 HA)` | Only leading and trailing whitespace in the source unit name is removed; values are not converted. For example, (1000 MT) means thousand metric tons. |
| `unit_raw` | Original unit text | `(1000 HA)           ` | Preserves original formatting, including whitespace, in the source unit description for traceability; refers to the same unit as unit. |
| `value` | Measure value | `140.0000` | Exact value retained in source units; null is not zero. Use with commodity, region, marketing year, measure, and unit. |
| `raw_value` | Original source value | `140.0000` | Preserves the original numeric text or missing-value marker for checking value; use the parsed number for normal analysis. For historical Excel files, this is the stored value read by the reader, which may differ from the rounded value displayed in the interface. |
| `source_release_period` | Source record update year and month | `2026-09` | Year-month label constructed from calendarYear and month. Only the month is known; do not invent a release date on the first or last day of that month. |


## Time, provenance, and version fields

| CSV column | Meaning | Actual example value | Interpretation |
|---|---|---|---|
| `source_release_date` | Source release date | `\N` | The publication or update date explicitly provided by the source. It is neither the year described by the data nor the date you downloaded the file; see this page for its dataset-specific meaning. |
| `source_release_at_utc` | Source release timestamp (UTC) | `\N` | A complete, evidence-backed release timestamp normalized to UTC. Do not invent a time when only a date or month is known, or when the timezone is unavailable; this is usually stored as \N. |
| `release_time_precision` | Release time precision | `month` | How precisely the source release time is known: timestamp for an exact instant, date/day for a day, month for a month, and unknown when it cannot be established. This is not numeric decimal precision. |
| `retrieved_at_utc` | Local retrieval time (UTC) | `2026-11-15 13:24:52.794186+00:00` | When the source file associated with this snapshot was first retrieved or imported into the local cache. Offline fixture replay also generates a local import receipt; this timestamp cannot establish when the data first became public. |
| `source_artifact_id` | Raw file fingerprint | `0ae6a975fde796058332efac6d16703a75f5834a07b717d8de99502e549bcb15` | SHA-256 of the raw response, CSV, PDF, or ZIP, used to locate and verify the source file. It is not a commodity, region, or report-row identifier. |
| `snapshot_id` | Processed version identifier | `unpublished` | Identifies a normalized version produced from the source file together with the parser, field definitions, and configuration. Reprocessing the same source may produce a new version; do not treat it as economic time or a business key. |
| `vintage_type` | Data vintage type | `current_revised` | report_vintage preserves values as published in a specific report; current_revised is the historical series available at download time, possibly revised; forecast_vintage preserves a specific forecast release. |

## Usage boundaries

- `source_release_period` has only month precision; exact release dates and UTC timestamps remain null in the current interface.
- `vintage_type=current_revised` denotes the current revised series; changing its time label cannot turn it into the original values of an earlier report.
- `region_mapping_status=absent_in_source_dictionary` indicates a missing entry in the upstream region dictionary; no region name is filled in without evidence.

Example values come from fixed official PSD response fixtures. For more details, see the [PSD technical guide](../psd.md).
