# CSV field guide: start with one row

This guide explains the business meaning of each CSV column, the units of its values, and common interpretation pitfalls. Field names are kept exactly as they appear in the code, with explanations in English; examples come from existing repository CSVs, not invented data.

To understand the data, choose a dataset below, then read "**How to read one row**" and "**Which columns to inspect first**"; consult the accompanying schema for precise types, nullability, and composite keys.

## Find a dataset

| Dataset | What one row generally represents | Guide and complete field definitions |
|---|---|---|
| WASDE | One value for a region, commodity, period, and attribute in a specific report release | [Definitions of all 30 columns](fields/wasde.md) |
| Export Sales | Eight sales/shipment measures for a commodity, destination, marketing year, and week | [Definitions of all 29 columns](fields/export_sales.md) |
| Costs and Returns | One cost/return measure for a region, enterprise type, year, and methodology | [Definitions of all 29 columns](fields/costs_returns.md) |
| World Agricultural Production | One current PSD measure or a cell in an original production/reliability report table | [How to read the data](fields/world_production.md) · [All 35 columns](fields/report_fields.md) |
| Grain Trade | One current PSD measure or a cell in an original grain supply/use/trade report table | [How to read the data](fields/grain_trade.md) · [All 35 columns](fields/report_fields.md) |
| Oilseed Trade | One current PSD measure or a cell in an original oilseed/meal/oil report table | [How to read the data](fields/oilseed_trade.md) · [All 35 columns](fields/report_fields.md) |
| RMA Summary of Business | A summary for a combination of state/county, crop, year, insurance plan, and coverage conditions | [Definitions of all 40 columns](fields/rma_sob.md) |

The three report datasets share column names and therefore use one complete field table, with separate business explanations and actual row examples for each. For the 27 columns in the standalone auxiliary PSD interface, see the [PSD field guide](fields/psd.md). The PDF-table parsing layer alone has 26 columns, corresponding to the section from `report_family` through `vintage_type` in the shared report field table.

## Fields that are easy to confuse

| Field | Plain-language explanation |
|---|---|
| `weeklyExports` | Quantity actually shipped for export during this week |
| `outstandingSales` | Unshipped sales commitments as of this week, scheduled for delivery in the current marketing year |
| `currentMYNetSales` | This week's net change in sales for the current marketing year; may be negative because of cancellations or adjustments |
| `marketYear`/`MarketYear` | The source's marketing-year code/label; it is not the report publication year and cannot be aligned directly across sources |
| `comparison_label=Change` | This row is a change, such as a downward forecast revision, rather than production or export volume itself |
| `total_premium` | RMA total premium before subsidies, not the policyholder's out-of-pocket premium |
| `loss_ratio` | Indemnities divided by premiums; 1.5 means 150%, not 1.5% |
| `retrieved_at_utc` | When the file entered the current local cache, not when the market data occurred |

For a full explanation of nulls, scales, years, and versions, see the **[common guide](fields/common.md)**.

## Suggested reading order

1. Identify the entity, region, and measure described by the row.
2. Identify the period: marketing year, calendar year, insurance year, or a forecast vintage from a particular report release.
3. Read the value together with its unit, especially distinguishing tons/thousand tons/million tons and percentages/ratios.
4. Check the status before handling nulls; `\N`, zero, not applicable, and not published are different cases.
5. Before joining or summing rows, check for regional totals, repeated release vintages, different sources, or different products.

## Basis for these explanations

The explanations were checked column by column against the current code, `schemas/`, and example CSVs. The 28 original RMA fields were also checked against the [official layout PDF (2026-05-28)](../test/fixtures/raw/rma-layout.pdf) retained in the repository; the abbreviation EFA, which that document does not explain, is explicitly marked as unknown here.

- [Seven CSVs and their download commands](../examples/README.md)
- [Field types, nullability, and composite key definitions](../schemas/)
- [Original expanded English schema reference](history/field_dictionary.schema-reference.md): retained as a historical technical reference, no longer the main reading entry point.

Direct RMA downloads currently use v2, while aggregate outputs may use v3; business columns and value interpretations are identical in both versions. When reading any historical export, use the `schema.json` beside that file as the authority.
