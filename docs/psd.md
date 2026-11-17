# Shared FAS PSD observations

> Reading guide: **[Data meaning, column-by-column explanations, and actual examples](fields/psd.md)**. The original English technical documentation is retained below.


```python
from usda_data import download_psd
frame = download_psd(["Corn"], [2025], data_dir="data")
```

```bash
python -m usda_data fetch --dataset psd --commodities Corn --market-years 2025 --data-dir data --output-dir data/exports
```

`psd` is a shared-layer diagnostic CLI target, not an eighth business dataset.
`list-datasets` still lists exactly the seven requested dataset IDs. Their three
FAS report interfaces and supplementary report tables are accepted in Phase 06.
`iter_psd` yields complete commodity/year partitions. Countries default to all,
including the separately retrieved official world series. Both interfaces retain
raw responses, dictionary versions, release inventories and normalized snapshots;
refresh rechecks requested partitions while retaining earlier versions.

The commodity/attribute union is frozen in docs/history/config/psd_scope.json and packaged with
the adapter. It contains 37 unique commodity codes: 18 required by World Agricultural
Production, 9 by Grain: World Markets and Trade, and 27 by Oilseeds: World Markets
and Trade, with overlap fetched once per family-union refresh operation. Coarse
grain components Millet and Mixed Grain are included. Local soybean, meal and oil
series remain distinct for local-marketing-year tables. Cotton is retained for
production reports. Unrelated coffee, fruit, dairy, meat and sugar families are
rejected. Table/page references and source report hashes document these boundaries.

The API returns commodityCode, countryCode, marketYear, calendarYear, month,
attributeId, unitId and value. Every field is preserved. Codes remain strings:
Corn is `0440000`, and world is `00`; zero prefixes are significant. Attributes
outside the frozen report-family union remain in raw files and are explicitly
counted in exclusion accounting. They are never silently dropped. Unknown
attributes or units fail even if they would otherwise fall outside the subset.

Country/all and world are independent endpoints. World values are official source
aggregates, not sums calculated by this package. European Union and other explicitly
identified regional aggregates retain `aggregation_level=region`; source residual
aggregates are separately marked. Ordinary country/historical-territory codes remain
country observations with their original descriptions. Regional membership metadata
is not an extra total. Never add world/region totals to their component countries.
Geographic code changes and historical groupings do not create a harmonized country
series. The official country dictionary refers to R15 for four residual/historical
geographies, but the region dictionary omits R15; retain the code, nullable region
name and `absent_in_source_dictionary` status instead of inventing a label.

Marketing-year IDs are preserved as supplied by PSD and must not be equated to ESR
IDs or calendar years. Local marketing-year and trade-year attributes (MY Imports
versus TY Imports/Exports) remain separate. The update calendarYear/month fields
are the source's latest record-update month; they can vary among countries in one
response. `source_release_period` retains that month. No publication day/time is
inferred: exact release-date/time fields remain null and precision is month.
Retrieval time remains separate. All API observations are `current_revised`, not
historical report vintages. Older report values cannot be reconstructed by relabeling
current API data with old publication dates.

Per-commodity dataReleaseDates returns country/year release inventory records
(commodityCode, countryCode, marketYear, releaseYear, releaseMonth), not a single
commodity-wide timestamp. The full source inventory is retained under manifests/psd/
periods and can establish actual available years at the Phase 09 cutoff. An inventory
entry does not promise unavailable historical monthly vintages.

Values are exact Decimals in original source units. Unit descriptions/scales are
retained, including their raw padded representation; normalized unit labels trim
outer whitespace only. Area, production and yield units cannot be mixed. Cotton
uses its actual source bales/yield units, not a blanket metric-ton conversion.
Missing attributes remain absent, not invented zero observations.

Independent balance tests use US Corn local-marketing-year quantities for 2024 and
2025: beginning stocks + production + MY imports = total supply; MY exports +
domestic consumption + ending stocks = total distribution; total supply = total
distribution. Only aligned unitId 8 components are used, with zero tolerance.
No invalid world-total, trade-year or cross-vintage balance is imposed.

Completeness checks include source-array decoding, exact field/key validation,
record accounting and independent US-country endpoint equality. The API documents
no pagination or response-count envelope. Tests cannot guarantee that an upstream
service never omits internal records; deterministic fixtures also use independently
pinned expected counts. Available report-only reliability tables, changes from prior
month and other supplementary metrics remain required Phase 06 work. Passing this
shared layer does not claim that the three report datasets are complete.
