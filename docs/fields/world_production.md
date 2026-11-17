# World Agricultural Production: how to read the CSV

[Back to the field guide](../field_dictionary.md) · [Example CSV](../../examples/world-production.csv) · **[Definitions of all 35 columns](report_fields.md)**

## What this file helps you understand

How much area a crop occupies in a region, its yield and total production, and how a particular report revises forecasts. Original reports also include forecast-reliability statistics, so not every row is a production quantity.

## Read two records from the example

**PSD row:** `observation_kind=psd_current`, `row_label=World`, `column_commodity=Corn`, `indicator=Yield`, `period_label=2025`, `value=6.2148`, `unit=(MT/HA)`.

This means that in the current PSD data, **world corn yield for marketing-year identifier 2025 is 6.2148 metric tons per hectare**. It is neither the original value from a specific historical report in 2025 nor total production.

**PDF row:** `observation_kind=report_table`, `report_period=2026-11`, table `TABLE 18 Reliability of Production Projections`, `section_label=BARLEY`, `row_label=United States`, measure `90 percent confidence interval`, value `2.5 Percent`.

This means that the **U.S. barley production projection reliability table** in the November 2026 report lists a statistic related to a 90% confidence interval, with a displayed value of 2.5%. It does not mean U.S. barley production is 2.5; the commodity is in `section_label`, so `column_commodity=not_applicable` does not indicate missing commodity information.

## Choose fields for your task

| What you want to examine | What to check first |
|---|---|
| A country's supply/use or production series for a crop | Select `psd_current`, then commodity, region, `period_label`, `indicator`, and `unit` |
| A forecast as published in a particular report | Select `report_table`, then `report_period`, the original table, and the comparison column |
| The size of a forecast revision | Check whether `comparison_label` and `indicator` denote a change or rate of change; do not treat it as total production |
| Products with special definitions, such as rice and cotton | Use the original table's product definitions and units rather than directly applying calculations for other grains |

Area, yield, and production relationships can be checked only when commodity, measurement basis, period, units, and vintage all match. Rice yield and production in the original table may use rough-rice and milled-rice bases respectively and cannot be multiplied directly.

Every column in this file is explained in the [shared field table](report_fields.md); see the [common guide](common.md) for time, nulls, and scales. The original detailed source documentation is retained in [world_production.md](../world_production.md).
