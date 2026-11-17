# FAS export sales

```python
from usda_data import download_export_sales
frame = download_export_sales(["corn", "soybeans", "wheat"], [2026], data_dir="data")
```

```bash
python -m usda_data fetch --dataset export-sales --commodities corn,soybeans,wheat --market-years 2026 --data-dir data --output-dir data/exports
```

`iter_export_sales` yields one validated commodity/marketing-year partition at a
time. Both public functions retain raw API responses, versioned dictionaries,
complete-partition snapshots and acquisition receipts. `countries="all"` is the
default. Destination code/name filtering happens after full partition validation.
`refresh=True` refetches every requested year, including older years. It never
assumes that only the newest year changes, and it keeps earlier snapshots.

Authentication uses USDA_FAS_API_KEY from the environment or `.env` in the working
directory, read at call time. No key is passed in URLs or CLI arguments, emitted
in logs, or persisted in manifests. Missing access fails explicitly. This
workstation's proxy cannot connect to api.fas.usda.gov, while direct authenticated
TLS succeeds. The explicit `[fas_http] trust_environment=false` setting in
config/datasets.toml is loaded by FAS clients. USDA_DATA_CONFIG can select another
configuration; change this transport setting when using a network requiring a
proxy. Other source transports retain their default proxy behavior.

Verified dictionary fields and all 44 official commodities are frozen in
docs/history/config/esr_inventory.json. All commodities remain in scope, including wheat
classes, oilseed products, cotton, rice, hides, beef and pork. `wheat` resolves to
All Wheat; class-level commodities keep their own codes and must not be added to
All Wheat. Destination dictionaries include aggregates and unknown destinations;
keep official codes and optional GENC values rather than pretending every row is
an independent geographic country. Regional membership is metadata, not extra
region-total observations.

The observation endpoint is a complete JSON array keyed by commodityCode,
countryCode, the requested marketYear, weekEndingDate and unitId. Its exact fields
are these dimensions (marketYear comes from the request) and eight distinct metrics:
weeklyExports, accumulatedExports, outstandingSales, grossNewSales,
currentMYNetSales, currentMYTotalCommitment, nextMYOutstandingSales and nextMYNetSales.
All source fields are accounted. Unknown fields or dictionary codes fail.

Weekly exports are shipments, accumulated exports are marketing-year shipments to
date, outstanding sales are unshipped commitments, and gross/new net sales are
separate source metrics. Current- and next-marketing-year sales are never combined.
Negative net sales represent valid cancellations/adjustments and are retained.
Metric quantities use the official unit: Metric Tons, Running Bales, Pieces, or
other dictionary denominations. No blanket conversion or acreage naming applies.

The marketing-year argument is the source endpoint identifier, not the calendar
year of the week. Source release dictionaries provide the current commodity's
marketing-year start/end. A boundary week may occur in two adjacent market-year
responses; both records remain distinct. In pinned wheat responses, June 5, 2025
appears in 2025 and 2026 partitions. The adapter does not shift or discard either.

API historical observations are current-revised captures, not original report
vintages. Latest commodity-level releaseTimeStamp is preserved separately as an
unzoned raw string. It is not substituted for historical per-week publication
time. Those source_release_date/source_release_at_utc fields remain null with
unknown precision when no partition-specific publication evidence exists.

The verified endpoint specification exposes no pagination or total-record field.
Completeness checks therefore combine full-array decoding, exact field/record
accounting, unique complete keys, transport truncation detection and independent
country-specific endpoint comparisons. Two pinned country responses each contain
53 records and equal their all-country subsets exactly; the live suite repeats
one comparison using fresh responses. A saved fixture's independently acquired
record count is also enforced in deterministic tests. These checks cannot prove
that the upstream service itself never omits a record; no such claim is made.
An empty source array is recorded explicitly, and cannot on its own establish
historical first availability or permanent source unavailability during backfill.

Decimal metric values and source raw numeric representations survive CSV reload.
Business keys include source marketYear, so reused boundary dates are valid. The
CLI atomically selects a complete export only after every requested partition
succeeds. All older raw and normalized versions remain addressable by hash.
