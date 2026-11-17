# Current business-table field dictionary

Generated from the versioned schema contracts. Earlier schema versions remain available for earlier snapshots; the selected export sidecar always governs a file.

## ers_costs_returns version 1

Machine-readable contract: `schemas/ers_costs_returns.v1.json`. CSV null token: `\N`; literal leading backslashes are escaped.

| Field | Type | Nullable | Business key | Meaning | Source mapping | Unit | Missing rule |
|---|---|---|---|---|---|---|---|
| commodity | string | False | True | commodity | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| enterprise_type | string | False | True | enterprise type | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| region | string | False | True | region | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| country | string | False | True | country | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| size | string | False | True | size | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| year_label | string | False | True | year label | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| series_family | string | False | True | series family | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| methodology | string | False | True | methodology | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| table_title | string | False | True | table title | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| category | string | False | True | category | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| item | string | False | True | item | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| unit | string | False | True | unit | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| forecast_vintage | string | False | True | forecast vintage | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| classification | string | False | True | classification | official field or source table metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| year | integer | False | False | Observation year; original label retained | Year/year header | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| value | decimal | True | False | Exact stored source value, no rounding or floating-point aggregation | Value/cell | unit column | Explicit null; zero remains zero; source markers retained separately |
| raw_value | string | False | False | Source lexical or BIFF stored numeric representation | source cell | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| value_status | string | False | False | reported/missing/unavailable/suppressed/not_applicable | source marker | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| estimate_status | string | False | False | Only explicit source statuses; otherwise unknown | year suffix/forecast source | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_item | string | False | False | Unmodified source item text | Item/row label | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_extra | string | False | False | Original additional source fields, codes and notes | source record | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_locator | string | False | False | CSV record or sheet/cell locator; not a business key | source position | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_date | date | True | False | Official last-update date if provided; historical forecast month is not an exact date | landing page | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_at_utc | datetime | True | False | Unknown precise release time stays null | official source | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| release_time_precision | string | False | False | date or unknown | source metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| retrieved_at_utc | datetime | False | False | UTC retrieval time | acquisition receipt | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_artifact_id | string | False | False | Original file/ZIP SHA256 | raw archive | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| snapshot_id | string | False | False | Parser/schema/config version identity | normalized snapshot | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| vintage_type | string | False | False | current_revised or forecast_vintage | source family | not_applicable | Explicit null; zero remains zero; source markers retained separately |

## esr_weekly_sales version 1

Machine-readable contract: `schemas/esr_weekly_sales.v1.json`. CSV null token: `\N`; literal leading backslashes are escaped.

| Field | Type | Nullable | Business key | Meaning | Source mapping | Unit | Missing rule |
|---|---|---|---|---|---|---|---|
| commodityCode | string | False | True | Official ESR commodity code | commodityCode | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| countryCode | string | False | True | Official destination/aggregate code | countryCode | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| marketYear | string | False | True | Marketing-year identifier supplied to the endpoint, not inferred from week date | request marketYear | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| weekEndingDate | date | False | True | Official week ending; boundary weeks may appear in adjacent MY partitions | weekEndingDate | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| unitId | string | False | True | Official source quantity unit code | unitId | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| commodity_name | string | False | False | Official commodity/class label | commodities.commodityName | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| destination_name | string | False | False | Official country/aggregate label | countries.countryDescription | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| region_id | string | False | False | Official destination-region membership, not an extra aggregate row | countries.regionId | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| region_name | string | False | False | Region label | regions.regionName | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| genc_code | string | True | False | Optional official geography code; null stays null | countries.gencCode | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| unit | string | False | False | Source quantity scale/denomination | unitsOfMeasure.unitNames | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| weeklyExports | decimal | True | False | Distinct official ESR metric; signed values retained | weeklyExports | unit column | Explicit null; zero remains zero; source markers retained separately |
| accumulatedExports | decimal | True | False | Distinct official ESR metric; signed values retained | accumulatedExports | unit column | Explicit null; zero remains zero; source markers retained separately |
| outstandingSales | decimal | True | False | Distinct official ESR metric; signed values retained | outstandingSales | unit column | Explicit null; zero remains zero; source markers retained separately |
| grossNewSales | decimal | True | False | Distinct official ESR metric; signed values retained | grossNewSales | unit column | Explicit null; zero remains zero; source markers retained separately |
| currentMYNetSales | decimal | True | False | Distinct official ESR metric; signed values retained | currentMYNetSales | unit column | Explicit null; zero remains zero; source markers retained separately |
| currentMYTotalCommitment | decimal | True | False | Distinct official ESR metric; signed values retained | currentMYTotalCommitment | unit column | Explicit null; zero remains zero; source markers retained separately |
| nextMYOutstandingSales | decimal | True | False | Distinct official ESR metric; signed values retained | nextMYOutstandingSales | unit column | Explicit null; zero remains zero; source markers retained separately |
| nextMYNetSales | decimal | True | False | Distinct official ESR metric; signed values retained | nextMYNetSales | unit column | Explicit null; zero remains zero; source markers retained separately |
| raw_metrics | string | False | False | Exact lexical numeric or null representations | source JSON | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_week_raw | string | False | False | Original source week-ending timestamp, no timezone invented | weekEndingDate | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| commodity_release_timestamp_raw | string | False | False | Latest commodity-level API release metadata; not historical report publication time | datareleasedates.releaseTimeStamp | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_date | date | True | False | Unknown historical per-partition publication date | not asserted from commodity-level latest release | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_at_utc | datetime | True | False | Unknown exact historical publication instant | source does not provide a zoned partition release timestamp | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| release_time_precision | string | False | False | unknown for historical partition publication | source metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| retrieved_at_utc | datetime | False | False | UTC response capture | receipt | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_artifact_id | string | False | False | Response bytes SHA256 | raw storage | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| snapshot_id | string | False | False | Parser/schema/config/artifact identity | normalized manifest | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| vintage_type | string | False | False | Current revised weekly historical series | API source semantics | not_applicable | Explicit null; zero remains zero; source markers retained separately |

## fas_dataset_observations version 1

Machine-readable contract: `schemas/fas_dataset_observations.v1.json`. CSV null token: `\N`; literal leading backslashes are escaped.

| Field | Type | Nullable | Business key | Meaning | Source mapping | Unit | Missing rule |
|---|---|---|---|---|---|---|---|
| report_family | string | False | True | report family | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| report_period | string | False | True | report period | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| table_title | string | False | True | table title | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| section_label | string | False | True | section label | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| section_product_type | string | False | True | section product type | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| row_label | string | False | True | row label | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| column_commodity | string | False | True | column commodity | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| indicator | string | False | True | indicator | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| period_label | string | False | True | period label | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| comparison_label | string | False | True | comparison label | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| unit | string | False | True | unit | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| value | decimal | True | False | Exact displayed report value | numeric cell | unit column | Explicit null; zero remains zero; source markers retained separately |
| raw_value | string | False | False | Original displayed number or missing marker | numeric cell | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| value_status | string | False | False | reported, not_reported or not_applicable | source marker | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| period_basis | string | False | False | Original table period definition, including MY versus TY | table caption and notes | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| table_metadata_id | string | False | False | Hash of complete header/notes/mapping metadata; does not replace business dimensions | table metadata archive | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_page | integer | False | False | First source page of this observation | PDF page | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_occurrences | integer | False | False | Number of explicitly investigated identical repeated source cells | source duplicate accounting | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_locations | string | False | False | All physical source locators and lexical values for repeated cells | PDF table positions | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_date | date | True | False | Official exact publication date when independently verified; otherwise null | report discovery metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_at_utc | datetime | True | False | No exact publication clock inferred | source metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| release_time_precision | string | False | False | day when verified, otherwise month | embedded month/date evidence | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| retrieved_at_utc | datetime | False | False | Artifact capture time | acquisition receipt | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_artifact_id | string | False | False | Original PDF bytes SHA256 | raw archive | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| snapshot_id | string | False | False | Parser/schema/config/source identity | normalized manifest | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| vintage_type | string | False | False | report_vintage, never current API relabelled as historical | source PDF | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| commodity_code | string | False | True | commodity code | original PSD code or not_applicable for report-only source classifications | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| geography_code | string | False | True | geography code | original PSD code or not_applicable for report-only source classifications | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| attribute_code | string | False | True | attribute code | original PSD code or not_applicable for report-only source classifications | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| unit_code | string | False | True | unit code | original PSD code or not_applicable for report-only source classifications | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| observation_kind | string | False | True | observation kind | original PSD code or not_applicable for report-only source classifications | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_calendar_year | string | False | False | Original PSD update year, not report date | calendarYear or not_applicable | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_month | string | False | False | Original PSD update month | month or not_applicable | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| aggregation_level | string | False | False | Source geographic aggregation class | PSD metadata or report_defined | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_region_code | string | False | False | Source PSD region membership | regionCode or not_applicable | not_applicable | Explicit null; zero remains zero; source markers retained separately |

## fas_report_observations version 1

Machine-readable contract: `schemas/fas_report_observations.v1.json`. CSV null token: `\N`; literal leading backslashes are escaped.

| Field | Type | Nullable | Business key | Meaning | Source mapping | Unit | Missing rule |
|---|---|---|---|---|---|---|---|
| report_family | string | False | True | report family | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| report_period | string | False | True | report period | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| table_title | string | False | True | table title | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| section_label | string | False | True | section label | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| section_product_type | string | False | True | section product type | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| row_label | string | False | True | row label | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| column_commodity | string | False | True | column commodity | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| indicator | string | False | True | indicator | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| period_label | string | False | True | period label | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| comparison_label | string | False | True | comparison label | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| unit | string | False | True | unit | original report table labels / documented whitespace normalization | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| value | decimal | True | False | Exact displayed report value | numeric cell | unit column | Explicit null; zero remains zero; source markers retained separately |
| raw_value | string | False | False | Original displayed number or missing marker | numeric cell | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| value_status | string | False | False | reported, not_reported or not_applicable | source marker | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| period_basis | string | False | False | Original table period definition, including MY versus TY | table caption and notes | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| table_metadata_id | string | False | False | Hash of complete header/notes/mapping metadata; does not replace business dimensions | table metadata archive | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_page | integer | False | False | First source page of this observation | PDF page | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_occurrences | integer | False | False | Number of explicitly investigated identical repeated source cells | source duplicate accounting | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_locations | string | False | False | All physical source locators and lexical values for repeated cells | PDF table positions | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_date | date | True | False | Official exact publication date when independently verified; otherwise null | report discovery metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_at_utc | datetime | True | False | No exact publication clock inferred | source metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| release_time_precision | string | False | False | day when verified, otherwise month | embedded month/date evidence | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| retrieved_at_utc | datetime | False | False | Artifact capture time | acquisition receipt | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_artifact_id | string | False | False | Original PDF bytes SHA256 | raw archive | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| snapshot_id | string | False | False | Parser/schema/config/source identity | normalized manifest | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| vintage_type | string | False | False | report_vintage, never current API relabelled as historical | source PDF | not_applicable | Explicit null; zero remains zero; source markers retained separately |

## psd_observations version 1

Machine-readable contract: `schemas/psd_observations.v1.json`. CSV null token: `\N`; literal leading backslashes are escaped.

| Field | Type | Nullable | Business key | Meaning | Source mapping | Unit | Missing rule |
|---|---|---|---|---|---|---|---|
| commodityCode | string | False | True | Original seven-digit commodity code, leading zeros retained | commodityCode | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| countryCode | string | False | True | Original country/aggregate code; 00 denotes source world endpoint | countryCode | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| aggregation_level | string | False | True | country, region, residual_aggregate or world | verified endpoint and country dictionary | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| marketYear | string | False | True | Source marketing-year identifier, not converted to calendar year | marketYear | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| attributeId | string | False | True | Official attribute code | attributeId | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| unitId | string | False | True | Official original unit/scale code | unitId | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| calendarYear | string | False | False | Source record update year; not original report vintage | calendarYear | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| month | string | False | False | Source update month, retaining leading zero | month | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| commodity_name | string | False | False | Official commodity description | commodities.commodityName | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| geography_name | string | False | False | Official geography description | countries.countryName or world endpoint | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| region_code | string | False | False | Membership metadata; not an additional total | countries.regionCode or R00 | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| region_name | string | True | False | Official region name; null when source countries refer to an absent region dictionary row | regions.regionName | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| region_mapping_status | string | False | False | resolved or absent_in_source_dictionary; original region code is always retained | dictionary cross-reference | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| genc_code | string | True | False | Optional source geography code | countries.gencCode | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| attribute_name | string | False | False | Official attribute label | commodityAttributes.attributeName | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| unit | string | False | False | Source unit description with surrounding whitespace trimmed only | unitsOfMeasure.unitDescription | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| unit_raw | string | False | False | Original unit descriptor including lexical padding | unitsOfMeasure.unitDescription | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| value | decimal | True | False | Exact numeric value in original source unit; missing not zero | value | unit column | Explicit null; zero remains zero; source markers retained separately |
| raw_value | string | False | False | Original numeric or null representation | value | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_period | string | False | False | Source year-month update label, not invented exact date | calendarYear and month | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_date | date | True | False | Exact publication day unavailable | source does not provide day | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_at_utc | datetime | True | False | Exact publication instant unavailable | source does not provide time | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| release_time_precision | string | False | False | month; no day or clock inferred | source year-month metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| retrieved_at_utc | datetime | False | False | UTC capture timestamp | receipt | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_artifact_id | string | False | False | Exact response hash | raw archive | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| snapshot_id | string | False | False | Version-aware snapshot identity | normalized manifest | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| vintage_type | string | False | False | current_revised; never historic report vintage | PSD API semantics | not_applicable | Explicit null; zero remains zero; source markers retained separately |

## rma_sob version 3

Machine-readable contract: `schemas/rma_sob.v3.json`. CSV null token: `\N`; literal leading backslashes are escaped.

| Field | Type | Nullable | Business key | Meaning | Source mapping | Unit | Missing rule |
|---|---|---|---|---|---|---|---|
| commodity_year | string | False | True | commodity year | Official 1989-forward SOB coverage-level field 1 | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| state_code | string | False | True | state code | Official 1989-forward SOB coverage-level field 2 | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| state_abbreviation | string | False | True | state abbreviation | Official 1989-forward SOB coverage-level field 3 | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| county_code | string | False | True | county code | Official 1989-forward SOB coverage-level field 4 | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| county_name | string | False | True | county name | Official 1989-forward SOB coverage-level field 5 | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| commodity_code | string | False | True | commodity code | Official 1989-forward SOB coverage-level field 6 | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| commodity_name | string | False | True | commodity name | Official 1989-forward SOB coverage-level field 7 | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| insurance_plan_code | string | False | True | insurance plan code | Official 1989-forward SOB coverage-level field 8 | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| insurance_plan_name | string | False | True | insurance plan name | Official 1989-forward SOB coverage-level field 9 | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| coverage_category | string | False | True | coverage category | Official 1989-forward SOB coverage-level field 10 | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| delivery_type | string | False | True | delivery type | Official 1989-forward SOB coverage-level field 11 | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| coverage_level | decimal | False | True | coverage level | Official 1989-forward SOB coverage-level field 12 | ratio | Explicit null; zero remains zero; source markers retained separately |
| policies_sold | integer | True | False | policies sold | Official 1989-forward SOB coverage-level field 13 | count | Explicit null; zero remains zero; source markers retained separately |
| policies_earning_premium | integer | True | False | policies earning premium | Official 1989-forward SOB coverage-level field 14 | count | Explicit null; zero remains zero; source markers retained separately |
| policies_indemnified | integer | True | False | policies indemnified | Official 1989-forward SOB coverage-level field 15 | count | Explicit null; zero remains zero; source markers retained separately |
| units_earning_premium | integer | True | False | units earning premium | Official 1989-forward SOB coverage-level field 16 | count | Explicit null; zero remains zero; source markers retained separately |
| units_indemnified | integer | True | False | units indemnified | Official 1989-forward SOB coverage-level field 17 | count | Explicit null; zero remains zero; source markers retained separately |
| quantity_type | string | False | True | quantity type | Official 1989-forward SOB coverage-level field 18 | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| net_reported_quantity | integer | True | False | net reported quantity | Official 1989-forward SOB coverage-level field 19 | source quantity_type | Explicit null; zero remains zero; source markers retained separately |
| endorsed_companion_acres | integer | True | False | endorsed companion acres | Official 1989-forward SOB coverage-level field 20 | Acres | Explicit null; zero remains zero; source markers retained separately |
| liability_amount | integer | True | False | liability amount | Official 1989-forward SOB coverage-level field 21 | USD | Explicit null; zero remains zero; source markers retained separately |
| total_premium | integer | True | False | total premium | Official 1989-forward SOB coverage-level field 22 | USD | Explicit null; zero remains zero; source markers retained separately |
| subsidy_amount | integer | True | False | subsidy amount | Official 1989-forward SOB coverage-level field 23 | USD | Explicit null; zero remains zero; source markers retained separately |
| state_private_subsidy | integer | True | False | state private subsidy | Official 1989-forward SOB coverage-level field 24 | USD | Explicit null; zero remains zero; source markers retained separately |
| additional_subsidy | integer | True | False | additional subsidy | Official 1989-forward SOB coverage-level field 25 | USD | Explicit null; zero remains zero; source markers retained separately |
| efa_premium_discount | integer | True | False | efa premium discount | Official 1989-forward SOB coverage-level field 26 | USD | Explicit null; zero remains zero; source markers retained separately |
| indemnity_amount | integer | True | False | indemnity amount | Official 1989-forward SOB coverage-level field 27 | USD | Explicit null; zero remains zero; source markers retained separately |
| loss_ratio | decimal | True | False | loss ratio | Official 1989-forward SOB coverage-level field 28 | ratio | Explicit null; zero remains zero; source markers retained separately |
| raw_record | string | False | False | Original pipe row excluding terminator; source NUL is encoded as literal Unicode escape for SQL portability; exact bytes remain in raw archive | raw source | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| missing_fields | string | False | False | Explicit missing-value field list; zeros stay zero | blank numeric fields | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| count_availability | string | False | False | CLIP counts unavailable per official layout; source raw values remain | layout CLIP note | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_member | string | False | False | Original ZIP member | ZIP directory | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_line | integer | False | False | One-based source line locator, not a key | raw text record | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_date | date | True | False | Publication day unknown; Last-Modified is transport metadata | source does not provide date | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_at_utc | datetime | True | False | Unknown exact source release time | source metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| release_time_precision | string | False | False | unknown | source metadata | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| retrieved_at_utc | datetime | False | False | UTC artifact capture time | receipt | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_artifact_id | string | False | False | Exact ZIP bytes SHA256 | raw storage | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| snapshot_id | string | False | False | Versioned normalized partition identity | storage manifest | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| vintage_type | string | False | False | current_revised commodity-year capture | RMA source semantics | not_applicable | Explicit null; zero remains zero; source markers retained separately |

## wasde_observations version 2

Machine-readable contract: `schemas/wasde_observations.v2.json`. CSV null token: `\N`; literal leading backslashes are escaped.

| Field | Type | Nullable | Business key | Meaning | Source mapping | Unit | Missing rule |
|---|---|---|---|---|---|---|---|
| WasdeNumber | string | False | True | Original source label; explicit sentinels only for documented empty optional dimensions | WasdeNumber | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| ReportDate | string | False | False | Original source label; explicit sentinels only for documented empty optional dimensions | ReportDate | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| ReportTitle | string | False | True | Original source label; explicit sentinels only for documented empty optional dimensions | ReportTitle | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| Attribute | string | False | True | Original source label; explicit sentinels only for documented empty optional dimensions | Attribute | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| ReliabilityProjection | string | False | True | Original source label; explicit sentinels only for documented empty optional dimensions | ReliabilityProjection | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| Commodity | string | False | True | Original source label; explicit sentinels only for documented empty optional dimensions | Commodity | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| Region | string | False | True | Original source label; explicit sentinels only for documented empty optional dimensions | Region | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| MarketYear | string | False | True | Original source label; explicit sentinels only for documented empty optional dimensions | MarketYear | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| ProjEstFlag | string | False | True | Original source label; explicit sentinels only for documented empty optional dimensions | ProjEstFlag | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| AnnualQuarterFlag | string | False | True | Original source label; explicit sentinels only for documented empty optional dimensions | AnnualQuarterFlag | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| Value | decimal | True | False | Exact reported numeric value; source markers remain in raw_value | Value | Unit column | Explicit null; zero remains zero; source markers retained separately |
| Unit | string | False | True | Original source label; explicit sentinels only for documented empty optional dimensions | Unit | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| ReleaseDate | string | False | False | Original source label; explicit sentinels only for documented empty optional dimensions | ReleaseDate | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| ReleaseTime | string | False | False | Original source label; explicit sentinels only for documented empty optional dimensions | ReleaseTime | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| ForecastYear | string | False | True | Original source label; explicit sentinels only for documented empty optional dimensions | ForecastYear | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| ForecastMonth | string | False | True | Original source label; explicit sentinels only for documented empty optional dimensions | ForecastMonth | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_date | date | False | True | Report publication date, inclusive request filter | ReleaseDate | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_release_at_utc | datetime | True | False | Exact publication instant only when timezone independently verified | not inferred from time-only CSV | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| release_time_precision | string | False | False | Precision of confirmed UTC publication information | date | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| retrieved_at_utc | datetime | False | False | First receipt time for this snapshot | acquisition manifest | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_artifact_id | string | False | False | SHA-256 of original file or ZIP bytes | raw storage | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| snapshot_id | string | False | False | Version-aware normalized identity | storage manifest | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| vintage_type | string | False | False | Report-vintage rather than current-revised API series | WASDE report date | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| raw_value | string | False | False | Exact original numeric lexical value or marker | Value | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| value_status | string | False | False | reported/missing/suppressed/unavailable/not_applicable | Value marker | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| raw_optional_dimensions | string | False | False | Original empty/label values for optional classifications | ReliabilityProjection,MarketYear,ProjEstFlag | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_member | string | False | False | ZIP member or empty string for standalone CSV | ZIP inventory | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_dimension_repair | string | False | False | Evidence ID for an exact-source dimension repair; empty if none | versioned repair registry | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_original_dimensions | string | False | False | Original dimension values before an independently evidenced repair | original CSV record | not_applicable | Explicit null; zero remains zero; source markers retained separately |
| source_conflict | string | False | False | Known cross-format numeric discrepancy; CSV value retained | versioned repair registry | not_applicable | Explicit null; zero remains zero; source markers retained separately |

