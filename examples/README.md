# CSV examples for seven datasets

Each dataset has exactly one final processed CSV containing 200 rows. These files are excerpts of the full command outputs, not the complete download results. All columns, types, nulls, and numeric precision follow the original output conventions.

These examples were generated offline by `test/tools/verify_examples.py` using fixed official test fixtures, with full Python and CLI outputs verified to match. Source data was not downloaded again during this run; retrieval times, snapshot IDs, and subsequently revised values may differ from a fresh download.

| Dataset | CSV | Example rows / full request rows in this run | Field definitions |
|---|---|---:|---|
| WASDE | [wasde.csv](wasde.csv) | 200 / 5,054 | [wasde_observations.v2.json](../schemas/wasde_observations.v2.json) |
| Costs and Returns | [costs-returns.csv](costs-returns.csv) | 200 / 257 | [ers_costs_returns.v1.json](../schemas/ers_costs_returns.v1.json) |
| Export Sales | [export-sales.csv](export-sales.csv) | 200 / 553 | [esr_weekly_sales.v1.json](../schemas/esr_weekly_sales.v1.json) |
| RMA Summary of Business | [rma-sob.csv](rma-sob.csv) | 200 / 155,676 | [rma_sob.v2.json](../schemas/rma_sob.v2.json) |
| World Agricultural Production | [world-production.csv](world-production.csv) | 200 / 7,967 | [fas_dataset_observations.v1.json](../schemas/fas_dataset_observations.v1.json) |
| Grain Trade | [grain-trade.csv](grain-trade.csv) | 200 / 8,643 | [fas_dataset_observations.v1.json](../schemas/fas_dataset_observations.v1.json) |
| Oilseed Trade | [oilseed-trade.csv](oilseed-trade.csv) | 200 / 9,947 | [fas_dataset_observations.v1.json](../schemas/fas_dataset_observations.v1.json) |

**Field guide: [What each column means, its units, and how to read a row](../docs/field_dictionary.md).** For dataset-specific units, years, aggregation boundaries, and source limitations, see the corresponding documentation in the [README](../README.md).

## Generate an example with one command

Run from the repository root after completing the installation in the README. Export Sales and the three report datasets require a FAS API key, configured through an environment variable or a local `.env` file. The commands below download and validate the specified scope before saving an excerpt. Raw files and normalized caches are stored in `data/`; temporary full exports are removed automatically. The target CSV is written only after the request succeeds, and the dataset's entry in `manifest.json` in the same directory is updated at the same time.

### WASDE: `wasde`

```bash
.venv/bin/python scripts/download_example.py --dataset wasde --start 2026-11-10 --end 2026-11-10 --rows 200 --example-output examples/wasde.csv --data-dir data
```

### Costs and Returns: `costs-returns`

```bash
.venv/bin/python scripts/download_example.py --dataset costs-returns --years 2025 --commodities Corn --rows 200 --example-output examples/costs-returns.csv --data-dir data
```

### Export Sales: `export-sales`

```bash
.venv/bin/python scripts/download_example.py --dataset export-sales --commodities 701 --market-years 2026 --rows 200 --example-output examples/export-sales.csv --data-dir data
```

### RMA Summary of Business: `rma-sob`

```bash
.venv/bin/python scripts/download_example.py --dataset rma-sob --commodity-years 2025 --rows 200 --example-output examples/rma-sob.csv --data-dir data
```

### World Agricultural Production: `world-production`

```bash
.venv/bin/python scripts/download_example.py --dataset world-production --market-years 2025 --commodities 0440000 --report-start 2026-11-01 --report-end 2026-11-30 --rows 200 --example-output examples/world-production.csv --data-dir data
```

### Grain Trade: `grain-trade`

```bash
.venv/bin/python scripts/download_example.py --dataset grain-trade --market-years 2025 --commodities 0440000 --report-start 2026-11-01 --report-end 2026-11-30 --rows 200 --example-output examples/grain-trade.csv --data-dir data
```

### Oilseed Trade: `oilseed-trade`

```bash
.venv/bin/python scripts/download_example.py --dataset oilseed-trade --market-years 2025 --commodities 2222000 --report-start 2026-11-01 --report-end 2026-11-30 --rows 200 --example-output examples/oilseed-trade.csv --data-dir data
```

## Excerpt rules and complete data

- WASDE, Export Sales, Costs and Returns, and RMA: take the first 200 rows in full-output order.
- The three report datasets: take the first 100 `psd_current` rows and the first 100 `report_table` rows to show both API data and original PDF tables; if either category has fewer than 100 rows, retain all available rows in that category.
- `--rows` adjusts the excerpt limit; it is an example-generator option, not a record limit for the download CLI.
- Commodity/country filters in report commands apply only to the PSD portion; tables for the specified report months are still parsed in full.
- To download a complete CSV, use the direct CLI form below or the `fetch_command` in each `manifest.json` entry.

```bash
.venv/bin/python -m usda_data fetch --dataset wasde --start 2026-11-10 --end 2026-11-10 --data-dir data --output-dir data/exports
```

In the CLI output directory, `csv_path` in `<dataset>.latest.json` points to the final CSV, and `schema_path` points to its field definitions. The filename is usually `<dataset>/<hash>/data.csv`.

`manifest.json` records commands, parameters, actual row counts, SHA-256 hashes for full outputs and excerpts, schemas, and source snapshot IDs. Do not overwrite the CSV after automatic conversion by spreadsheet software: leading zeros in codes, exact decimals, and the `\N` null representation must be preserved.

Direct RMA downloads currently use schema v2; the full aggregation tool can upgrade approved historical descriptions to v3. Both versions have identical business fields, types, and CSV values; the v3 field dictionary also explains this example.
