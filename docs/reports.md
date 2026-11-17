# Three FAS report datasets

The three business datasets combine current-revised PSD observations with original
report-vintage numerical cells. `observation_kind` and `vintage_type` make the two
sources explicit. They are not interchangeable versions of the same historical
series. No current API value is relabeled with an old report date.

```python
from usda_data import download_dataset, download_reports
frame = download_dataset(
    "world-production", market_years=[2025], commodities=["Corn"],
    report_start="2026-11-01", report_end="2026-11-30", data_dir="data")
manifest = download_reports("world-production", "2026-11-01", "2026-11-30", data_dir="data")
```

```bash
python -m usda_data fetch --dataset world-production --market-years 2025 --commodities Corn --report-start 2026-11-01 --report-end 2026-11-30 --with-reports --data-dir data --output-dir data/exports
```

Replace the dataset ID with grain-trade or oilseed-trade; for the latter a sample
PSD commodity is `2222000` (soybeans). Omitting a commodity filter requests the
entire frozen family scope. Source marketing years and report publication dates
are separate required options. Commodity/country filters select the requested PSD
sample; report tables in the requested publication interval remain complete and
carry explicit original dimensions. Attachments are retained as parsing evidence,
with `--with-reports` making this archival intent explicit. `download_reports`
returns manifests only; structured report cells come from `download_dataset`.

Public report discovery uses the official PSD CircularsHandler month inventory,
then verifies each attachment's family and embedded month. A directory month is a
candidate, not proof of source availability. Exact publication time is read from
the matching official article's title metadata; related-article timestamps are not
used. Verified article URLs for the development/holdout months are recorded with
discovery hashes. Where only a month is available, preserve month precision and
require full-month request bounds rather than inventing a day. Missing discovery
months stay unresolved for full-backfill reconciliation.

The unified schema retains table title, section, section product type, row label,
column commodity, indicator, source period label, prior/current comparison column,
unit, report month, source code dimensions and observation kind. For report cells
without official codes, `not_applicable` means a source label is authoritative; no
invented numeric code replaces it. PSD codes, aggregation levels and source update
month remain explicit. Page/line locators are provenance, never substitute keys.
Every report table has full original header/footnote text retained in metadata.

Required table scope was frozen before final parser testing: all numbered world
production/oilseed tables, grain appendix supply/trade tables, and every explicit
trade/outlook changes table in report bodies. Narrative paragraphs, illustrative
charts/maps, calendars and contact lists are explicitly excluded. `config/
report_table_inventory.json` records the decisions; `config/report_coverage.csv`
records actual extraction status by family, month and table. No available required
table in the tested October/November 2026 layouts is left unresolved.

The focused parser supports production area/yield/production plus changes, world
crop production country columns, production reliability statistics, six-year
country/commodity tables, three-commodity year blocks, historical attribute-column
tables, and merged-cell trade/outlook changes tables including continuations.
Additional year instances of an already validated changes-table type are parsed
rather than omitted. Unknown table types, missing mandatory families, changed
numeric widths, unpaired cells and conflicting duplicate dimensions fail.

Identical printed duplicates (for example Canada/Brazil rows in an oilseed trade
table) become one business cell with `source_occurrences` and all source locations.
This is explicitly investigated source duplication, not silent deduplication.
Different values under identical dimensions are a blocking error. Input cells
reconcile to output occurrences. `nr` and dash cells retain distinct missing
statuses; zero remains reported zero. Negative changes remain signed.

Values preserve the displayed Decimal precision. Exact source-value comparisons
use zero tolerance. Any PSD/report numerical comparison requires independently
evidenced aligned vintage, matching commodity/geography/period/indicator/unit and
an explicit scale. Different vintages are recorded as such, never accepted as a
same-vintage numerical match. A same-vintage dimension/unit/value discrepancy fails.
The October versus November world-wheat production change is preserved as a real
report-vintage difference; month-only API update metadata does not prove exact
publication alignment.

Historical report layout variants outside the accepted October/November 2026
families are not silently claimed supported. Full archive reconciliation and any
additional available required layouts must pass Phase 09 before full backfill is
accepted. Report download, structured extraction and current PSD availability are
separate statuses. Raw PDF files and normalized revisions remain reproducible.
