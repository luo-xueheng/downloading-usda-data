# WASDE observations

> 中文阅读入口：**[数据含义、逐列解释和真实示例](fields/wasde.md)**。下面保留原有英文技术说明。


`download_wasde(start, end, *, data_dir="data", refresh=False)` returns an exact-value
pandas DataFrame. `iter_wasde` yields one publication partition at a time. Dates
are inclusive official publication dates, not observation years or retrieval dates.

```python
from usda_data import download_wasde
frame = download_wasde("2026-11-10", "2026-11-10", data_dir="data")
```

```bash
python -m usda_data fetch --dataset wasde --start 2026-11-10 --end 2026-11-10 --data-dir data --output-dir data/exports
```

The current monthly CSV is the complete selected structured format. It covers all
28 observed November 2026 table families, including meat, eggs, milk, dairy prices,
quarterly animal products, wheat classes and reliability statistics. Historical
ZIPs use the same ordered 16-field source contract, beginning April 2010. Earlier
unsupported layouts are not represented as downloaded history. Source field labels,
including spelling and double spaces, survive normalization. Unknown layouts fail.
The frozen early fixture contains 68 report dates and 329,315 records; this count
is an inventory, not a claim that the full backfill has run.

The key includes report release date/number, table title, attribute, reliability
classification, commodity (including actual classes), geography, source market
year, estimate/projection label, annual/quarter designation, unit, forecast year and
month. Reliability tables have no single observation market year: an explicit
`not_applicable` category preserves that absence, while the original label survives
in `raw_optional_dimensions`. No reporting quarter or projection flag is collapsed.

`Value` is an exact Decimal; `raw_value` preserves its lexical precision. Empty,
unavailable, suppressed and not-applicable values have distinct statuses. Zero is
never missing. `source_release_date` is confirmed from ReleaseDate. The time-only
CSV field remains in ReleaseTime; a timezone is not silently inferred for historical
files, so exact UTC publication time remains null and precision is date. Retrieval
time is separate. Stocks are point-in-time amounts; production, trade and use are
period flows. Units/scales vary by table and must not be aggregated indiscriminately.
World totals must not be added to their constituent countries. Reliability metrics
are forecast-error statistics, not supply/use observations. No blanket balance
identity or universal percentage tolerance is imposed.

Where current XML is linked, original XML bytes, table titles and footnotes are
archived before publication. Summary tables provide a 360-cell independent XML/CSV
comparison for the development release at zero tolerance. Previous-month comparison
columns in XML are explicitly excluded from that current forecast comparison and
remain available in the raw artifact. XML is not claimed as a complete second parser.
Numerical cross-format conflicts block current publication and retain both sources.
The complete current CSV-to-XML family map is in the Phase 02 table coverage file.

The 2010-2015 ZIP has a source defect on May 11, 2011: seven Pork reliability records
lack the Production attribute and three lack Million Pounds units. A packaged,
versioned repair registry applies only when the entire original row and archive
SHA-256 match. PDF page 37 was visually reviewed, with original XML corroboration;
all original dimensions and repair evidence are retained. The Pork RMSE differs
between the structured CSV/XML (3.50/3.5) and PDF (3.4). The numeric output remains
the explicit CSV series and exposes this discrepancy in `source_conflict`; it does
not claim PDF equality or substitute a PDF numeric value. Unknown omissions fail.

Cache checks use original byte hashes. Repeated unchanged captures reuse normalized
snapshots while receipts retain checks. Changing parser, schema, configuration or
raw bytes creates a new snapshot. CLI export has an immutable content hash path;
`wasde.latest.json` switches only after every requested partition succeeds. A failed
job cannot select its partial CSV as a complete export. Each export has its own
schema sidecar, using `Schema.read_csv` for exact types and escaped-null semantics.

For historical files, a canonical ZIP access failure may use the same official USDA
CDN path, recording both the original failure and actual successful origin. Failed
or temporarily inaccessible sources are not declared permanently unavailable.
