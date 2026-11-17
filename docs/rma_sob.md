# RMA Summary of Business with coverage level

> 中文阅读入口：**[数据含义、逐列解释和真实示例](fields/rma_sob.md)**。下面保留原有英文技术说明。


```python
from usda_data import download_rma_sob, iter_rma_sob
frame = download_rma_sob([2025], data_dir="data")
for chunk in iter_rma_sob([2025], data_dir="data", chunk_size=5000):
    assert len(chunk) <= 5000
```

```bash
python -m usda_data fetch --dataset rma-sob --commodity-years 2025 --chunk-size 5000 --data-dir data --output-dir data/exports
```

The public DataFrame function materializes its requested result; use the iterator
or CLI for large requests. Raw ZIPs and the verified official layout are archived.
Annual normalized snapshots are published only after every source record validates
and a disk-backed complete-key index finds no duplicates. Changing the chunk size
changes neither data nor snapshot identity. The CLI selects its complete export
only after all requested years succeed, preserving earlier published versions.

The official May 28, 2026 layout has 28 pipe-delimited fields for commodity years
1989 forward. The parser verifies every member, row width, source year, fixed-width
code, category and numeric type. State/county/commodity/plan codes remain strings
with leading zeros. All grouping dimensions are keys: commodity year, state code
and abbreviation, county code/name, crop code/name, insurance plan code/name,
coverage category, delivery type, coverage level and quantity type. Neither source
line numbers nor opaque hashes replace these dimensions.

The source quantity_type is authoritative. Development/holdout files include Acres,
Pounds, Tons, Trees, Vines, Colonies, # of Clams, # of Shellfish and Not Reported.
`net_reported_quantity` is never universally called acreage. The separate
`endorsed_companion_acres` field is specifically acres. Money is reported in whole
USD, counts/quantities are integer source fields, coverage level is an exact
four-decimal ratio and loss_ratio is the source two-decimal ratio. Signed indemnity
adjustments and negative loss ratios are preserved. Other signed values in unsigned
layout fields are rejected for investigation.

Actual blank numeric fields remain null with explicit missing_fields and raw_record.
Zero remains zero. For a source CLIP insurance-plan label, policy/unit counts are
unavailable per the official layout; normalized counts stay null while original
raw values remain in raw_record. No count is fabricated. Source last-modified time
is transport metadata, not an exact official publication instant; release date/time
remain unknown while retrieval UTC is preserved separately.

`--all-history` discovers all currently listed supported coverage-level years,
starting at 1989. It explicitly reports 1948-1988 as a different unsupported
State/County/Commodity layout, rather than claiming it as coverage-level history.
A request for an unlisted year fails visibly. RMA commodity years are not report
publication years; future commodity-year files can legitimately be listed already.

Do not add state/region totals to their member county rows, or combine quantity
types. County 999 means All Other Counties, not an ordinary named county, and 000
requires explicit aggregate interpretation. Policy/unit counts can overlap across
products, plans or coverage options; summing them does not count unique farms or
policies. Endorsement and companion coverage can overlap base coverage quantities.
No universal farm-area total or loss-ratio sum is produced.

Acceptance subtotals are explicitly limited to disjoint source-row groups for
Alaska/Arizona leaf counties and Acres within each year. Rows missing any selected
subtotal component are separately excluded and counted. Those arithmetic sums are
checks of transformation, not claims about unique insured farms or nonoverlapping
base-plus-endorsement acreage. Money and quantity totals match independent integer
calculations at zero tolerance. An annual source revision replaces the complete
year snapshot; all older source bytes and snapshots remain reproducible.
