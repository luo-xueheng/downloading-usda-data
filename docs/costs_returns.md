# ERS commodity costs and returns

> 中文阅读入口：**[数据含义、逐列解释和真实示例](fields/costs_returns.md)**。下面保留原有英文技术说明。


`download_costs_returns(years, *, commodities="all", data_dir="data", refresh=False)`
returns an exact-value pandas DataFrame. `iter_costs_returns` yields one complete
source-file partition at a time, selecting the requested observation years from it.
Every update parses and replaces the entire source file; revisions to older years
and deleted source rows cannot remain hidden behind a newest-year-only update.

```python
from usda_data import download_costs_returns
frame = download_costs_returns([2025], commodities="Corn", data_dir="data")
```

```bash
python -m usda_data fetch --dataset costs-returns --years 2025 --commodities Corn --data-dir data --output-dir data/exports
```

Use comma-separated years or `YYYY:YYYY` inclusive bounds on the CLI. The default
commodity scope is all linked products; a commodity selection is only a requested
subset, not the frozen inventory. Forecast workbooks contain multiple crops and
are filtered after complete parsing. All hog enterprise variants remain separate.
Historical products can have no rows in a post-2010 request; they remain in the
inventory, and their full supported history can be selected explicitly.

The verified landing page lists 73 attachments: 17 Recent commodity/enterprise
pairs (CSV and XLSX), a current forecast pair, an archive with 14 forecast workbooks,
and 36 Historical products. All links have inclusion/exclusion reasons. Where CSV
and XLSX present the same numeric series, CSV is the selected source and XLSX is an
alternative presentation; both formats' layouts have been inspected and tested.
No organic or separately linked milk-production product is added to this scope.

The schema retains commodity, enterprise, region, country, size, observation year
and original year label, series family, methodology, actual table title, category,
item, unit, forecast vintage and any source column classification. These are the
business dimensions; worksheet/cell positions are provenance, never substitute
business keys. Source codes and explanatory fields from machine-readable XLSX
sheets are preserved in `source_extra`. Raw item labels and historical footnotes
also survive. Unknown columns, numeric markers, missing required dimensions,
unmapped numerical cells and duplicate business keys fail before publication.

Recent CSV/XLSX uses source survey-base labels for methodology. Legacy tables
retain separate cash and economic/full-ownership contexts, original titles and
sheet-period labels, even where a source mistakenly repeats a cash-cost title
above an economic-cost section. Those sections are distinguished using the actual
cost heading. Historical survey changes described only in notes remain attached;
the package does not assert comparability or create a cross-method spliced series.

Wide historical tables are unpivoted from explicit Item/year columns. Every
numerical cell outside a year header must map to an observation; missing cells in
recognized data rows remain missing. Repeated year blocks retain their crop class
and column-specific unit. Tobacco includes Flue-cured/Burley and per-acre/per-cwt
columns; milk includes per-cwt/per-cow tables. The source's tobacco curing-fuel `1/`
marker means its cost is included elsewhere, as stated in the worksheet note; it
is a null with `included_elsewhere` status, not a zero. Other unknown numeric
footnote markers are rejected.

Forecast vintages are distinct by original archive member. Their F-suffixed
observation years stay separate from the publication vintage. No date is inferred
from a month-only archive name. Estimate status is `unknown` unless the source
explicitly labels a forecast or estimate; the current date is never used to guess.
Landing-page last-update dates are retained separately from retrieval time and do
not become invented exact UTC release instants.

CSV numeric lexical values become Decimal directly. Historical BIFF/XLS and XLSX
workbook numerical cells retain the stored numeric representation returned by the
reader, converted using its shortest decimal string. Original raw values remain
available. Formatted spreadsheet display rounding is not silently substituted for
stored values. Source formulas are read from their saved cached results; the
package does not recalculate economics or spreadsheet formulas.

Operating costs and allocated overhead are distinct categories. Fixed independently
reviewed Corn U.S. total 2025 component lists are checked against two published
category totals. Rounding allowance is fixed before testing as `(components+1)*0.005`
dollars per planted acre, from separately rounded cent-level components and total.
Nested subtotals must not be double-counted. Negative residual returns are valid.
Costs per acre/cow/cwt are not aggregate dollar spending, and different units or
enterprise methods must not be added together.

Raw archives, acquisition receipts and versioned normalized file snapshots are
retained under data_dir. Refresh never deletes old versions. The CLI writes a
complete immutable export and atomically selects it only after every requested
file succeeds. Its schema sidecar supports exact CSV reload using `Schema.read_csv`.
An authentication, network, source-layout or validation failure exits nonzero.
