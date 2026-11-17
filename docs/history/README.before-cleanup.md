# downloading-usda-data

Versioned USDA downloads, pandas DataFrames, and exact CSV/SQL transfer for seven datasets. The frozen full backfill contains **9,987,892 rows**, acquired at the November 16, 2026 cutoff. The execution ledger and current handover gate are in [docs/execution_status.md](../execution_status.md); the evidence index is [docs/acceptance_index.md](../acceptance_index.md).

## Install

Use Python 3.11 or newer on a POSIX system (macOS/Linux; the writer lock uses `fcntl`). The clean-install acceptance runtime is Python 3.13.5. From this repository:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install '.[dev]'
```

This is a regular wheel installation. Development edits require reinstalling, or an explicitly chosen editable installation. Dependencies and supported version constraints are declared in `pyproject.toml`; the tested environment is recorded in the Phase 10 evidence.

## Minimal examples

Run these from the repository root after installation:

```bash
.venv/bin/python -m usda_data --help
.venv/bin/usda-data list-datasets
.venv/bin/python -m usda_data calendar --dataset all
.venv/bin/python -m usda_data fetch --dataset all --config config/full_backfill.json --dry-run
.venv/bin/python scripts/handover_examples.py --output-dir artifacts/acceptance/phase-10/examples
```

The last example executes both the public Python API and CLI for **every dataset**, using pinned official source fixtures in a separate local cache. It compares every returned field and proves the examples run without network access. It requires the development dependencies and the repository's fixtures. This demonstrates reproducibility; current source access is checked separately by the live tests.

Read a complete export in bounded chunks without changing codes, nulls or decimals:

```python
import json
from pathlib import Path
from usda_data.schema import Schema

root = Path("data/exports/datasets")
manifest = json.loads((root / "complete.latest.json").read_text())
selected = manifest["exports"]["wasde"]
schema = Schema.load(root / selected["schema_path"])
chunk = next(schema.read_csv_chunks(root / selected["csv_path"], chunk_size=1000))
assert len(chunk) == 1000
assert chunk["WasdeNumber"].map(type).eq(str).all()
```

Real downloads use the same functions and source-specific ranges; see [Python/CLI interfaces](../interfaces.md). FAS ESR/PSD require `USDA_FAS_API_KEY` in the environment or a working-directory `.env`. See [credential setup](../credential_setup.md). Keys are never command-line arguments or committed files.

## Data and operations

The authoritative seven-dataset manifest is `data/exports/datasets/complete.latest.json`. CSV and schema locations, exact hashes, component partitions and snapshot IDs are recorded there. Preserve the raw archives and versioned manifests when transferring data. [The handover guide](../handover.md) maps the original internship requirements to deliverables; [field dictionaries](../field_dictionary.md) document every current business-table field.

Use [SQL transfer](../sql_transfer.md) for an executable isolated SQLite import/readback example. [Backfill](../backfill.md) documents the full task configuration, and [updates/recovery](../updates_and_recovery.md) describes `sync`, checkpoints, exit codes and operator scheduling. No scheduler is installed.

Source-specific meanings: [WASDE](../wasde.md), [export sales](../export_sales.md), [production](../world_production.md), [grain](../grain_trade.md), [oilseeds](../oilseed_trade.md), [costs/returns](../costs_returns.md), [RMA](../rma_sob.md). [Release notes](../release_notes.md) distinguish publication rules from observed availability.

Known source limitations remain explicit: WASDE structured coverage starts April 2010; certain report months and June 2016 WAP Table 10 have evidenced source gaps; current-revised API history cannot reconstruct historical publication vintages. See the Phase 09 coverage manifest and gap evidence. Commodity/forecast years through 2027 may occur in files already available at the cutoff.
