# Oilseed Trade: how to read the CSV

[Back to the field guide](../field_dictionary.md) · [Example CSV](../../examples/oilseed-trade.csv) · **[Definitions of all 35 columns](report_fields.md)**

## What this file helps you understand

Production, crushing, consumption, imports, exports, and stocks of oilseeds, protein meals, and vegetable oils, along with forecast changes in reports. Soybeans, soybean meal, and soybean oil are different products, not three names for the same commodity.

## Read two records from the example

**PSD row:** `row_label=World`, `column_commodity=Oilseed, Soybean`, `indicator=Domestic Consumption`, `period_label=2025`, `value=433053.0000`, `unit=(1000 MT)`.

This means that in the current PSD series, **world soybean domestic consumption for that marketing-year identifier is 433,053 thousand metric tons**. This measures consumption of soybeans as a product; directly adding soybean meal/oil consumption does not produce an unduplicated consumption total.

**PDF row:** from the November 2026 report's `2025/26 OUTLOOK CHANGES` table, with `row_label=Brazil`, `column_commodity=Meal, Soybean`, `indicator=Exports`, `comparison_label=Change`, and a value of `-190 Thousand Metric Tons`.

This means that the report **revised Brazil's 2025/26 soybean meal export forecast downward by 190,000 metric tons**. The negative sign indicates the direction of the forecast change, not a negative total export volume for Brazil.

## Common pitfalls

- `section_product_type` distinguishes repeated Total/Other labels within the Oilseed, Meal, and Oil categories; do not merge using only `row_label`.
- A `comparison_label=Change` value is a change; confirm the measure and comparison column before deciding whether it belongs in an export-volume time series.
- Area rows may still use hectares, while quantity rows use tons; a main table title mentioning tons does not imply that every column uses tons.
- Unreported-value markers such as `nr` are not zero. Source tables are rounded, so displayed components may not sum exactly to the displayed total.

See the [shared field table](report_fields.md) for all columns and the [common guide](common.md) for nulls and scales. The original detailed source documentation is retained in [oilseed_trade.md](../oilseed_trade.md).
