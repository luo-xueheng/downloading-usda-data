# Grain Trade: how to read the CSV

[Back to the field guide](../field_dictionary.md) · [Example CSV](../../examples/grain-trade.csv) · **[Definitions of all 35 columns](report_fields.md)**

## What this file helps you understand

Production, consumption, trade, and stocks for grains such as wheat, rice, and corn, and how a particular report revises those values. The file contains both current revised PSD series and original report tables; check `observation_kind` first.

## Read two records from the example

**PSD row:** `row_label=World`, `column_commodity=Corn`, `indicator=TY Exports`, `period_label=2025`, `value=207552.0000`, `unit=(1000 MT)`.

This means that in PSD, **world corn trade-year exports for that year identifier are 207,552 thousand metric tons**. TY denotes a trade-year basis and cannot be arbitrarily replaced with a calendar-year or local marketing-year basis.

**PDF row:** from the November 2026 `All Grain Summary Comparison` table, with `row_label=Other`, `column_commodity=Corn`, `indicator=Domestic Consumption`, `period_label=2024/25`, `value=941.0`, `unit=Million Metric Tons`.

This means that in the original table, **corn domestic consumption for the aggregate category Other is 941 million metric tons**. Other is a grouping defined by the original table, not a country named "Other"; interpret its scope together with the table's other groupings.

## Common pitfalls

- `Exports` is an export measure; `TY Exports` explicitly uses a trade-year basis. Measures named imports/exports in different tables do not necessarily cover the same period.
- `Previous`, `Current`, and `Change` mean the previous value, current value, and difference respectively; they cannot be added to obtain total exports.
- World, regional totals, member countries, Other, and Subtotal may overlap; do not sum the entire CSV directly.
- `Domestic Consumption` and `Feed Dom. Consumption` are not independent totals at the same level; feed consumption may already be included in domestic consumption.

See the [shared field table](report_fields.md) for all columns and the [common guide](common.md) for units and periods. The original detailed source documentation is retained in [grain_trade.md](../grain_trade.md).
