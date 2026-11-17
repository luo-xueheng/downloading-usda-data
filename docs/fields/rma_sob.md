# Agricultural insurance business (RMA): field guide

[Back to the field guide](../field_dictionary.md) · [Common conventions and nulls](common.md) · [Machine-readable field definitions](../../schemas/rma_sob.v2.json)

## What this dataset describes

Insurance business data summarized by crop insurance year, state, county, crop, insurance plan, and coverage conditions. Each row summarizes one combination of conditions, including policy/insurance-unit counts, insured quantities, premiums, subsidies, and indemnities; it is neither an individual policy nor an individual farmer. Direct downloads use schema v2, while aggregation can upgrade to v3; columns, types, and CSV values are identical in both versions.

## How to read one row

In the first row of [rma-sob.csv](../../examples/rma-sob.csv), for "All Other Crops" in Southeast Fairbanks, Alaska, in 2025 under the APH plan at 50% coverage, the net reported quantity is **200 acres**, the premium before subsidies is **$1449**, indemnities are **$29930**, and the loss ratio is **20.66 times**. Do not read this as a 20.66% loss ratio or treat the 2 policies sold as 2 distinct farmers.

## Which columns to inspect first

First identify `commodity_year`, state/county, crop, insurance plan, and `coverage_level`. For insured quantities, use `net_reported_quantity` and `quantity_type`; for monetary amounts, use the respective amount columns; for counts, check `count_availability` first.

The table below covers all 40 current fields. Values come from fixed repository examples and may be drawn from different records; do not combine the example-value column into a single record. Long JSON strings and identifiers are abbreviated with ellipses. The `schema.json` beside the export is authoritative for types, nullability, and the complete composite key.

## Business and verification fields

| CSV column | Meaning | Actual example value | Interpretation |
|---|---|---|---|
| `commodity_year` | Crop/insurance year | `2025` | Usually corresponds to the crop's normal harvest year and identifies the policy year providing coverage. It is not the year the insurance data were published or downloaded. |
| `state_code` | State FIPS code | `02` | Two-digit code for the state containing the insured farm; 02 is Alaska. Preserve leading zeros; a state code alone is not a nationally unique farm identifier. |
| `state_abbreviation` | State abbreviation | `AK` | U.S. postal state abbreviation, such as AK (Alaska) or AL (Alabama). |
| `county_code` | County FIPS/aggregate code | `240` | Three-digit county code, used together with state_code. 999 denotes special aggregates such as All Other Counties and must not automatically be treated as an ordinary county. |
| `county_name` | County or county-level aggregate name | `Southeast Fairbanks` | For example, Southeast Fairbanks; All Other Counties is an aggregate label for other counties. |
| `commodity_code` | RMA commodity code | `9999` | Four-digit crop/product code used in insurance business, such as 0041 for corn in the examples. It cannot be joined directly to ESR or PSD codes. |
| `commodity_name` | Insured commodity name | `All Other Crops` | Crop/product covered by the policy. All Other Crops is the source table's aggregate for other crops, not a specific crop variety. |
| `insurance_plan_code` | Insurance plan code | `90` | Official code for the selected insurance coverage plan, not a coverage proportion. Use insurance_plan_name to help identify it. |
| `insurance_plan_name` | Insurance plan abbreviation | `APH` | Examples include APH (Actual Production History), RP (Revenue Protection), and WFRP (Whole-Farm Revenue Protection). The basis to which the coverage level applies varies by plan. |
| `coverage_category` | Coverage category | `A` | A means Buyup, C means CAT (catastrophic coverage), E means Existing Coverage Policy, and L means Limited Coverage. These are category codes, not ratings. |
| `delivery_type` | Insurance delivery/reinsurance category | `RBUP` | RBUP means reinsured buyup, RCAT means reinsured catastrophic coverage, FBUP means federal buyup, and FCAT means federal catastrophic coverage. Original codes are retained to avoid confusion with coverage_category. |
| `coverage_level` | Coverage level | `0.5000` | Decimal proportion, such as 0.5000 for 50%. The basis varies by plan and may be production, revenue, an amount, or inventory; it cannot always be interpreted as fixed production coverage. |
| `policies_sold` | Policies sold | `2` | Number of policies sold as reported to RMA, not a deduplicated count of insured farmers. Stored as null when these counts are unavailable for CLIP plans. |
| `policies_earning_premium` | Policies earning premium | `1` | Officially defined as policies for which acreage has been reported to RMA, not policies for which premium payment has actually been received. |
| `policies_indemnified` | Policies with reported losses | `1` | Officially defined as policies for which losses have been reported to RMA; do not simply recalculate it using indemnity_amount > 0. |
| `units_earning_premium` | Insurance units earning premium | `1` | Number of insurance units with reported acreage. Here, unit means an insurance unit, not a unit of measurement or a farmer count. |
| `units_indemnified` | Insurance units with reported losses | `1` | Number of insurance units with reported losses. This differs from policy counts, since one policy may involve multiple units. |
| `quantity_type` | Insured quantity unit/type | `Acres` | Examples include Acres, Tons, Pounds, and Trees. Not Reported means the type was not specified; do not default to acres. |
| `net_reported_quantity` | Quantity adjusted for the insured share | `200` | Net quantity after adjustments such as multiplying reported planted quantity by the policyholder's interest share; must be used with quantity_type. Not all rows represent area. |
| `endorsed_companion_acres` | Endorsement/companion-option acres | `0` | Acreage insured through endorsements or companion options, always measured in acres. May overlap with base coverage acreage and cannot be added directly to obtain unique acreage. |
| `liability_amount` | Insurance liability amount | `45100` | Maximum insurance coverage amount for this record, in dollars. It is not an amount already paid as indemnities. |
| `total_premium` | Total premium before subsidies | `1449` | Premium amount before subsidies, in dollars; not the policyholder's final out-of-pocket premium. |
| `subsidy_amount` | Premium subsidy amount | `971` | Subsidized premium amount for this record, in dollars. Other subsidy fields are retained separately and are not arbitrarily merged here. |
| `state_private_subsidy` | State/private subsidy | `0` | Subsidy amount supplied by a state government or private entity, in dollars; distinct from the general subsidy field. |
| `additional_subsidy` | Additional program subsidy | `0` | Additional subsidy from a program or another process, in dollars. The official layout states that in 2021 and 2022 this field contains Pandemic Cover Crop Program amounts; do not apply that interpretation to every year. |
| `efa_premium_discount` | EFA premium discount amount | `0` | In dollars. The official 2026-05-28 layout lists the name but leaves the definition blank; the repository lacks sufficient evidence to expand EFA further and retains the original field. |
| `indemnity_amount` | Indemnity/loss amount | `29930` | Indemnity amount for this record, in dollars. The source allows signed adjustments; do not automatically replace negative values with zero. |
| `loss_ratio` | Loss ratio | `20.66` | indemnity_amount ÷ total_premium. 1 means indemnities equal premiums, 0.5 means approximately 50%, and 20.66 means approximately 20.66 times, not 20.66%. The source value is retained rather than recalculated and overwritten row by row. |
| `raw_record` | Original pipe-delimited record | `2025&#124;02&#124;AK&#124;240&#124;Southeast Fairbanks           &#124;9999&#124;All Other Crop…` | Preserves the entire source TXT line, with fields separated by vertical bars. Source NUL characters are written as literal Unicode escapes for SQL readability; exact original bytes remain in the source ZIP. |
| `missing_fields` | Missing fields | `[]` | JSON array listing fields whose values were originally absent or unavailable under the rules; [] means no missing fields are listed. Read with count_availability. |
| `count_availability` | Availability of policy/unit counts | `reported_source_values` | reported_source_values means source counts are retained; when CLIP counts are unavailable, the corresponding status is recorded and these count fields are set to null, not zero. |
| `source_member` | Source TXT filename inside the ZIP | `sobcov_2025.txt` | For example, sobcov_2025.txt; used to locate the original file. |
| `source_line` | Source TXT line number | `1` | Original line number, starting at 1, for source verification; not a policy number and not a substitute for business fields when identifying records. |


## Time, provenance, and version fields

| CSV column | Meaning | Actual example value | Interpretation |
|---|---|---|---|
| `source_release_date` | Source release date | `\N` | The publication or update date explicitly provided by the source. It is neither the year described by the data nor the date you downloaded the file; see this page for its dataset-specific meaning. |
| `source_release_at_utc` | Source release timestamp (UTC) | `\N` | A complete, evidence-backed release timestamp normalized to UTC. Do not invent a time when only a date or month is known, or when the timezone is unavailable; this is usually stored as \N. |
| `release_time_precision` | Release time precision | `unknown` | How precisely the source release time is known: timestamp for an exact instant, date/day for a day, month for a month, and unknown when it cannot be established. This is not numeric decimal precision. |
| `retrieved_at_utc` | Local retrieval time (UTC) | `2026-11-17T12:57:06.466884+00:00` | When the source file associated with this snapshot was first retrieved or imported into the local cache. Offline fixture replay also generates a local import receipt; this timestamp cannot establish when the data first became public. |
| `source_artifact_id` | Raw file fingerprint | `c66d887d099c437327780238c9679ca1d1fd1350ab1dd42107ecee9382e74a58` | SHA-256 of the raw response, CSV, PDF, or ZIP, used to locate and verify the source file. It is not a commodity, region, or report-row identifier. |
| `snapshot_id` | Processed version identifier | `a79883b3e51715d328e431b6f9c729208fce160e2c207fea2cbe41b5527a09c9` | Identifies a normalized version produced from the source file together with the parser, field definitions, and configuration. Reprocessing the same source may produce a new version; do not treat it as economic time or a business key. |
| `vintage_type` | Data vintage type | `current_revised` | report_vintage preserves values as published in a specific report; current_revised is the historical series available at download time, possibly revised; forecast_vintage preserves a specific forecast release. |

## Units, nulls, and aggregation

- All monetary columns are in dollars; `coverage_level` and `loss_ratio` are proportions/ratios, not dollar amounts.
- Policy counts and insurance-unit counts are different. When CLIP counts are unavailable, keep them null; do not treat them as zero or derive substitutes from other fields.
- When `quantity_type` is Trees, Pounds, Tons, or similar, `net_reported_quantity` is not an area. Endorsement acreage may overlap with base coverage.
- To calculate an overall loss ratio across groups, first confirm that the groups do not overlap and use consistent definitions, then divide total indemnities by total premiums; do not sum row-level `loss_ratio` values. Do not force a ratio calculation when total premiums are zero.
- The current source does not provide sufficient evidence for the exact release date of each annual file; HTTP Last-Modified is not a verified release date either.

The business meanings of fields 1–28 were checked against the [official layout (2026-05-28)](../../test/fixtures/raw/rma-layout.pdf) retained in the repository. Its EFA definition is blank, so this page explicitly leaves it unknown. For more details, see the [RMA technical guide](../rma_sob.md).
