# Export Sales (ESR): field guide

[Back to the field guide](../field_dictionary.md) · [Common conventions and nulls](common.md) · [Machine-readable field definitions](../../schemas/esr_weekly_sales.v1.json)

## What this dataset describes

Describes sales and shipment progress for U.S. agricultural exports to a destination. Each row represents "commodity × destination × marketing year × reporting week × unit" and contains eight sales/export measures. Here, sales are commodity quantities, not dollar revenue.

## How to read one row

In [export-sales.csv](../../examples/export-sales.csv), for marketing year identifier 2026 and the week ending 2025-09-11, U.S. sorghum exports to Mexico were `4678` metric tons, accumulated exports were `4678` metric tons, outstanding sales were `64000` metric tons, and total commitments were `68678` metric tons. **4678 + 64000 = 68678**. Net sales that week were `4475` metric tons, which differs from the week's shipments.

## Which columns to inspect first

Select `commodity_name`, `destination_name`, and `marketYear`, then sort by `weekEndingDate`. Use `weeklyExports` for this week's shipments, `currentMYNetSales` for this week's sales changes, and `outstandingSales` for unshipped orders.

The table below covers all 29 current fields. Values come from fixed repository examples and may be drawn from different records; do not combine the example-value column into a single record. Long JSON strings and identifiers are abbreviated with ellipses. The `schema.json` beside the export is authoritative for types, nullability, and the complete composite key.

## Business and verification fields

| CSV column | Meaning | Actual example value | Interpretation |
|---|---|---|---|
| `commodityCode` | ESR commodity code | `701` | The Export Sales system's own commodity identifier. In the example, 701 is Sorghum; it is not a PSD or RMA commodity code. |
| `countryCode` | Destination code | `2010` | Official code for an export destination country, regional aggregate, or unknown destination. In the example, 2010 is Mexico, not a year. |
| `marketYear` | Marketing-year identifier for sales | `2026` | The marketing-year identifier used in this API query. Year boundaries vary by commodity; for example, marketYear=2026 records may occur in 2025. Do not replace it with the calendar year of weekEndingDate. |
| `weekEndingDate` | Reporting week end date | `2025-09-04` | The end of the statistical week covered by this record, not the report publication date. At a marketing-year boundary, the same week may appear in two year partitions. |
| `unitId` | Quantity unit code | `1` | Identifier in the official unit dictionary; use together with unit. The code itself is not a quantity. |
| `commodity_name` | Commodity name | `Sorghum` | Official name corresponding to the commodity code, possibly a subcategory such as a wheat class. Do not count a parent category and its subcategories together. |
| `destination_name` | Destination name | `MEXICO` | For example, MEXICO. It may also be a regional aggregate or an unknown destination; not every row is an individual country. |
| `region_id` | Destination region code | `11` | Regional membership from the destination dictionary. This is classification information, not an additional regional export total. |
| `region_name` | Destination region name | `WESTERN HEMISPHERE` | For example, WESTERN HEMISPHERE. Preserved from the source dictionary; it does not imply that historical regional definitions have been harmonized. |
| `genc_code` | GENC geographic code | `MEX` | Geographic identifier supplied by the source dictionary, such as MEX. If absent, it is \N; do not fill it arbitrarily using another coding system. |
| `unit` | Shared unit for the eight sales measures | `Metric Tons` | The example uses Metric Tons. Other commodities may use bales, pieces, or other units; do not treat all commodities as tons. |
| `weeklyExports` | Actual exports this week | `0` | Quantity actually shipped for export during this reporting week, representing fulfilled commitments rather than newly signed contracts. |
| `accumulatedExports` | Accumulated exports for this marketing year | `0` | Cumulative quantity exported from the start of the marketing year through this week. Weekly records are cumulative progress and must not be summed across weeks. |
| `outstandingSales` | Unshipped sales for the current year | `64203` | Unshipped sales commitments as of this week, scheduled for delivery in the current marketing year. This is a balance, not a weekly addition. |
| `grossNewSales` | Gross new sales this week | `203` | Gross additions to sales, reported separately from net sales after cancellations and adjustments. This is still a quantity, not dollar sales revenue. |
| `currentMYNetSales` | Net sales this week for the current year | `203` | This week's net sales change for the current marketing year, after new sales, cancellations, and relevant adjustments. It can be negative and does not equal this week's actual exports. |
| `currentMYTotalCommitment` | Total export commitments for the current year | `64203` | Current-year exports plus unshipped sales, conceptually accumulatedExports + outstandingSales. The field retains the official value and is not replaced with a formula during download. |
| `nextMYOutstandingSales` | Unshipped sales for the next marketing year | `0` | Unshipped sales commitments as of this week, scheduled for delivery in the next marketing year. Do not merge them into current-year outstandingSales. |
| `nextMYNetSales` | Net sales this week for the next year | `0` | This week's net sales change for delivery in the next marketing year. Recorded separately from current-year net sales and also subject to cancellations or adjustments. |
| `raw_metrics` | Source values for the eight measures | `{"accumulatedExports": "0", "currentMYNetSales": "203", "currentM…` | JSON string preserving the API's original numeric/null representations for these eight measures to support precision checks. |
| `source_week_raw` | Original week-ending timestamp text | `2025-09-04T00:00:00` | Original API weekEndingDate text, such as a string containing T00:00:00. It is not a release timestamp; the midnight value is not assumed to be UTC. |
| `commodity_release_timestamp_raw` | Original latest commodity release information | `2026-11-13T08:30:22.49` | Original commodity-level releaseTimeStamp text. It describes the latest release information in the dictionary, not the release date of this row's historical reporting week; no timezone is invented. |


## Time, provenance, and version fields

| CSV column | Meaning | Actual example value | Interpretation |
|---|---|---|---|
| `source_release_date` | Source release date | `\N` | The publication or update date explicitly provided by the source. It is neither the year described by the data nor the date you downloaded the file; see this page for its dataset-specific meaning. |
| `source_release_at_utc` | Source release timestamp (UTC) | `\N` | A complete, evidence-backed release timestamp normalized to UTC. Do not invent a time when only a date or month is known, or when the timezone is unavailable; this is usually stored as \N. |
| `release_time_precision` | Release time precision | `unknown` | How precisely the source release time is known: timestamp for an exact instant, date/day for a day, month for a month, and unknown when it cannot be established. This is not numeric decimal precision. |
| `retrieved_at_utc` | Local retrieval time (UTC) | `2026-11-17T12:57:06.312829+00:00` | When the source file associated with this snapshot was first retrieved or imported into the local cache. Offline fixture replay also generates a local import receipt; this timestamp cannot establish when the data first became public. |
| `source_artifact_id` | Raw file fingerprint | `20fa6d65e545db3be2e5ee3c3b610e27f1b1b1e6b9c795df0bd043a272ad820f` | SHA-256 of the raw response, CSV, PDF, or ZIP, used to locate and verify the source file. It is not a commodity, region, or report-row identifier. |
| `snapshot_id` | Processed version identifier | `61a32f014b4cb87e3320cca2a1bb56c36be64522d448cdad8da537e8930fff28` | Identifies a normalized version produced from the source file together with the parser, field definitions, and configuration. Reprocessing the same source may produce a new version; do not treat it as economic time or a business key. |
| `vintage_type` | Data vintage type | `current_revised` | report_vintage preserves values as published in a specific report; current_revised is the historical series available at download time, possibly revised; forecast_vintage preserves a specific forecast release. |

## Why the eight numbers cannot be added together

- Weekly quantities: `weeklyExports`, `grossNewSales`, `currentMYNetSales`, and `nextMYNetSales`. They measure different things.
- Year-to-date total: `accumulatedExports`. Each successive week includes earlier weeks, so summing them does not produce an annual total.
- Balances as of that week: `outstandingSales` and `nextMYOutstandingSales`. These are not weekly additions.
- Total commitments: `currentMYTotalCommitment` already includes accumulated current-year exports and unshipped sales; adding those two measures again would double-count them.
- Negative net sales can reflect cancellations/adjustments, not "negative shipments"; the current and next marketing years must also remain separate.
- The API provides the currently available revised series and does not automatically reconstruct the version first published for a historical week. The latest commodity-level timestamp is not used as the release date for every historical week.

For more source and processing details, see the [Export Sales technical guide](../export_sales.md).
