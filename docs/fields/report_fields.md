# The 35 columns shared by three FAS report datasets: field guide

[Back to the field guide](../field_dictionary.md) · [Common conventions and nulls](common.md) · [Machine-readable field definitions](../../schemas/fas_dataset_observations.v1.json)

## What this dataset describes

The World Agricultural Production, Grain Trade, and Oilseed Trade CSVs use the same column names. Each file contains two sources: current revised supply/use data from the PSD API and table cells from original PDF reports. Check `observation_kind` first to understand what the shared columns mean in a particular row.

## How to read one row

For example, `observation_kind=psd_current`, `row_label=World`, `column_commodity=Corn`, `indicator=Production`, and `period_label=2025` represent world corn production for that marketing year in the API. A separate `report_table` row may represent a change in the next year's forecast in a monthly PDF; the two must not be added directly.

## Which columns to inspect first

Select `observation_kind` first. For PSD rows, focus on commodity/region/measure codes, `period_label`, `value`, and `unit`; for PDF rows, focus on `report_period`, `table_title`, `section_label`, `row_label`, `column_commodity`, `indicator`, `period_label`, and `comparison_label`.

The table below covers all 35 current fields. Values come from fixed repository examples and may be drawn from different records; do not combine the example-value column into a single record. Long JSON strings and identifiers are abbreviated with ellipses. The `schema.json` beside the export is authoritative for types, nullability, and the complete composite key.

## Business and verification fields

| CSV column | Meaning | Actual example value | Interpretation |
|---|---|---|---|
| `report_family` | Report family | `world-production` | world-production means World Agricultural Production; grain-trade means Grain Trade; oilseed-trade means Oilseed Trade. All three use the same column structure but cover different commodities and measures. |
| `report_period` | Original report issue | `not_applicable` / `2026-11` | For report_table rows, this is the report month, such as 2026-11; for psd_current rows, it is not_applicable because current API values cannot be presented as an original report vintage. |
| `table_title` | Original table title | `PSD current-revised observations` | Identifies whether the row belongs to a supply/use, changes, or reliability table. PSD rows always use PSD current-revised observations. |
| `section_label` | Within-table group heading | `Yield` | A measure, commodity, or regional grouping within a table; its meaning varies by table. For example, BARLEY identifies barley in a reliability table, while other tables may use Domestic Consumption. |
| `section_product_type` | Within-table product category | `not_applicable` / `Oilseed` | Examples include Oilseed, Meal, and Oil. Distinguishes repeated Total/Other labels under different product categories; uses not_applicable when the original table does not require this classification. |
| `row_label` | Row label/statistical region | `World` | For PSD rows, the country or aggregate region name; for PDF rows, the original row label, which may be a country, World, Other, or another category. It cannot always be treated as a country name. |
| `column_commodity` | Commodity column label | `Corn` | Commodity name for PSD rows; the original column's commodity for PDF rows. Some reports identify the commodity in section_label or the table title, so this column may be not_applicable. |
| `indicator` | Statistical measure | `Yield` | Examples include Production, Yield, and Exports. Reliability tables also include errors, confidence intervals, and other measures; do not assume every row is production based on the dataset name. |
| `period_label` | Period described by the value | `2025` | For PSD rows, the marketing-year identifier, such as 2025; for PDF rows, the original label, such as 2025/26, or a historical statistical interval. Distinct from the report publication month in report_period. |
| `comparison_label` | Comparison column/revision category | `not_applicable` / `Change` | Previous is the previous value, Current is the current value, and Change is the difference; month labels such as Oct/Nov may also be retained. Uses not_applicable when no comparison applies. Changes may be negative. |
| `unit` | Unit of this cell's value | `(MT/HA)` | (1000 MT)/Thousand Metric Tons means thousand metric tons; Million Metric Tons means million metric tons; (MT/HA) means metric tons per hectare. Distinguish area, quantity, price, and percentage row by row. |
| `value` | Value of this cell | `6.2148` | Interpret together with the measure, period, comparison column, and unit. A Change row of -190 may mean a downward revision of 190 thousand metric tons, never a negative export volume. |
| `raw_value` | Original source value | `6.2148` | Preserves the original numeric text or missing-value marker for checking value; use the parsed number for normal analysis. For historical Excel files, this is the stored value read by the reader, which may differ from the rounded value displayed in the interface. |
| `value_status` | Value status | `reported` | Indicates whether the value is reported normally, missing, not applicable, not reported, or another status. Check this column before handling nulls; only reported denotes a normally reported number, and zero can still be reported. |
| `period_basis` | Period and measurement basis | `PSD source marketing-year identifier; TY measures retain their so…` | Preserves year definitions from headers/notes, such as MY (marketing year) versus TY (trade year). source-labelled period means only that the original label is retained, not that it has been harmonized to a calendar year. |
| `table_metadata_id` | Header and footnote metadata reference | `PSD dictionary snapshot 69e01ee04f13013d5e0c15fb603275647766c53c1…` | Refers to headers, notes, and mappings saved during parsing. Usually a hash for PDF tables; PSD rows may use PSD dictionary snapshot followed by an identifier. It is not the table's business name. |
| `source_page` | PDF page number | `0` | Physical page number in a PDF source, starting at 1; 0 for PSD rows means the source is not a PDF, not PDF page zero. |
| `source_occurrences` | Occurrences of the same source cell | `1` | Some original tables repeat identical business dimensions and values; after verification, these are merged and their occurrence count is recorded. Usually 1; do not multiply value by it. |
| `source_locations` | Original location details | `{"countryCode": "00", "attributeId": "184"}` | For PDF rows, a JSON list of locations (page, line, original value); for PSD rows, source locators such as country and measure codes. Used for traceability, not as another measure. |
| `commodity_code` | PSD commodity code | `0440000` | Only psd_current rows have the corresponding official code, such as 0440000 for corn. PDF rows are not forcibly mapped and use not_applicable; read the original commodity labels. |
| `geography_code` | PSD geographic code | `00` | PSD country or aggregate code; 00 means world. PDF rows use not_applicable even when row_label happens to be a country; no completed code mapping is claimed. |
| `attribute_code` | PSD measure code | `184` | Official measure code corresponding to indicator, such as 28 for Production and 184 for Yield. PDF rows are not forcibly mapped and use not_applicable. |
| `unit_code` | PSD unit code | `26` | Source unit-dictionary code; read with unit. PDF rows use not_applicable, while their actual unit remains in unit. |
| `observation_kind` | Value source type | `psd_current` | psd_current denotes the PSD API's current revised series; report_table denotes an original PDF report table. Filter this column first before analysis; do not add two sources describing the same fact. |
| `source_calendar_year` | PSD record update year | `2026` | calendarYear supplied by the API record, not the data's marketing year. PDF rows use not_applicable. |
| `source_month` | PSD record update month | `11` | month supplied by the API record, such as 11. Records in one response may have different update months; it is not an independently verified complete release date. PDF rows use not_applicable. |
| `aggregation_level` | Geographic aggregation level | `world` | For PSD, this can be country, region (regional total), world, or residual_aggregate (other/residual total); PDF rows use report_defined and must be interpreted from the original table. |
| `source_region_code` | PSD regional membership code | `R00` | The source region to which the record belongs, such as R00 or R12. This is geographic classification information, not an additional regional total. PDF rows use not_applicable. |


## Time, provenance, and version fields

| CSV column | Meaning | Actual example value | Interpretation |
|---|---|---|---|
| `source_release_date` | Source release date | `\N` / `2026-11-10` | The publication or update date explicitly provided by the source. It is neither the year described by the data nor the date you downloaded the file; see this page for its dataset-specific meaning. |
| `source_release_at_utc` | Source release timestamp (UTC) | `\N` / `2026-11-10T17:15:00+00:00` | A complete, evidence-backed release timestamp normalized to UTC. Do not invent a time when only a date or month is known, or when the timezone is unavailable; this is usually stored as \N. |
| `release_time_precision` | Release time precision | `month` | How precisely the source release time is known: timestamp for an exact instant, date/day for a day, month for a month, and unknown when it cannot be established. This is not numeric decimal precision. |
| `retrieved_at_utc` | Local retrieval time (UTC) | `2026-11-17T12:57:06.444204+00:00` | When the source file associated with this snapshot was first retrieved or imported into the local cache. Offline fixture replay also generates a local import receipt; this timestamp cannot establish when the data first became public. |
| `source_artifact_id` | Raw file fingerprint | `c664fb044e5f0ab81262960152b354d9ace9852e60926ddc753aedb4b1cae992` | SHA-256 of the raw response, CSV, PDF, or ZIP, used to locate and verify the source file. It is not a commodity, region, or report-row identifier. |
| `snapshot_id` | Processed version identifier | `69e01ee04f13013d5e0c15fb603275647766c53c1c45961af8d2def568677b36` | Identifies a normalized version produced from the source file together with the parser, field definitions, and configuration. Reprocessing the same source may produce a new version; do not treat it as economic time or a business key. |
| `vintage_type` | Data vintage type | `current_revised` | report_vintage preserves values as published in a specific report; current_revised is the historical series available at download time, possibly revised; forecast_vintage preserves a specific forecast release. |

## Field differences between the two sources

| Aspect | `psd_current` | `report_table` |
|---|---|---|
| Value vintage | Currently available revised series | Values published in the specified report at the time |
| Release month | Does not pretend to belong to a PDF issue; report_period is not_applicable | report_period is the original report month |
| Codes | Retains official PSD commodity/region/measure/unit codes | Not currently forced to align with PSD codes; uses not_applicable |
| Source page | 0, indicating a non-PDF source | Physical PDF page number, starting at 1 |
| Geographic interpretation | aggregation_level explicitly identifies country/region/world | report_defined; interpret using original table labels |
| Data update year/month | source_calendar_year / source_month | Not applicable |

World, regional, and member-country records overlap; Other/Total/Subtotal may also overlap. Do not sum all rows in the file unconditionally. MY means marketing year and TY means trade year; interpret their boundaries according to the original table and commodity.

The standalone `fas_report_observations.v1.json` contains only the first 26 columns described on this page, from `report_family` through `vintage_type`, and is used by the PDF parsing layer. The final nine columns on this page are additional source/code fields added by the three final datasets.
