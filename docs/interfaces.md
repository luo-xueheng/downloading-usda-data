# Public interfaces

All functions below return pandas DataFrames. Import them from `usda_data`.
Each call retains raw bytes, sanitized acquisition receipts and versioned normalized
snapshots beneath `data_dir="data"`. Repeated cached calls reuse artifacts;
`refresh=True` rechecks bytes and retains older versions. These convenience functions
materialize the requested result. Use `iter_wasde`, `iter_export_sales`, `iter_psd`,
`iter_costs_returns` or `iter_rma_sob`, or the streaming CLI, for large requests.

| Dataset | Python `download_dataset` options | CLI `fetch` options |
|---|---|---|
| `wasde` | `start="2026-11-10", end="2026-11-10"` | `--start 2026-11-10 --end 2026-11-10` |
| `export-sales` | `commodities=["701"], market_years=[2026]` | `--commodities 701 --market-years 2026` |
| `costs-returns` | `years=[2025], commodities="Corn"` | `--years 2025 --commodities Corn` |
| `rma-sob` | `commodity_years=[2025]` | `--commodity-years 2025` |
| `world-production` | `market_years=[2025], commodities=["0440000"], report_start="2026-11-01", report_end="2026-11-30"` | `--market-years 2025 --commodities 0440000 --report-start 2026-11-01 --report-end 2026-11-30` |
| `grain-trade` | Same options as production | Same options as production |
| `oilseed-trade` | Same options, with `commodities=["2222000"]` | Same options, with `--commodities 2222000` |

These are bounded interface samples, not the full scope. The executable
`scripts/handover_examples.py` runs every row above through both interfaces and
compares the complete typed results using pinned official fixtures. CLI requests
also accept `--data-dir`, `--output-dir`, and `--force` (the refresh equivalent).

Dedicated functions are `download_wasde(start,end)`,
`download_export_sales(commodities,market_years,countries="all")`,
`download_psd(commodities,market_years,countries="all")`,
`download_costs_returns(years,commodities="all")`, and
`download_rma_sob(commodity_years)`. Optional arguments are keyword-only.
`download_reports(report_family,start,end)` returns an attachment manifest and
archives PDFs; `download_dataset` returns structured report-family observations.
All seven accept `data_dir` and `refresh` through the public dispatcher. Unknown
options and missing required ranges raise `ConfigurationError`.

Dates are inclusive report publication bounds. Marketing years, ERS observation
years and RMA commodity years retain their source meanings. `--all-history` is
implemented for RMA only: coverage-level layouts from 1989 onward, with 1948–1988
explicitly unsupported. Other adapters reject this flag. Countries filter source
codes/names; overlapping aggregates must not be added to component countries.

`usda-data` and `python -m usda_data` invoke the same CLI. Exit 0 means successful
or confirmed unchanged processing; exit 1 means runtime, access, validation or
partial-run failure; exit 2 means invalid arguments. A credential failure cannot
publish a successful empty export. A valid source-empty response remains distinct.

The `config/datasets.toml` file contains HTTP settings. Full fetch/sync uses the
explicit tasks in `config/full_backfill.json`; `config/small_sync.json` is only an
integration sample. The full configuration is frozen at the recorded cutoff.
Future dates require a reviewed newly discovered task inventory. `--dry-run`
prints the configured tasks without numeric downloads; discovery planning can
read source metadata. Run calendar commands from the repository or pass an
explicit `--config` path. Wheels bundle parser metadata, not downloaded data or
operator-specific configurations.
