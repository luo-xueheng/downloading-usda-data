# Batch downloads and aggregation

`config/full_backfill.json` contains 805 tasks with a cutoff of 2026-11-16 and is suitable for replaying that scope. `config/small_sync.json` is a small-scope usage example covering all seven datasets. The original full-delivery guide and memory-budget records are retained in full in the [historical version](history/backfill.before-cleanup.md).

## Run an existing configuration

```bash
.venv/bin/python -m usda_data fetch --dataset all --config config/full_backfill.json --dry-run
.venv/bin/python -m usda_data fetch --dataset all --config config/full_backfill.json
```

After a failure, resume using the same data directory:

```bash
.venv/bin/python -m usda_data fetch --dataset all --config config/full_backfill.json --resume
```

Update the configured scope:

```bash
.venv/bin/python -m usda_data sync --config config/full_backfill.json
```

These commands store source files, normalized snapshots, and task recovery state in `data/`. Do not remove them while you still need to resume the same download.

## Discover a new download scope

Task planning reads current official catalogs and FAS metadata online and requires an API key. It records the discovery cutoff time and does not misrepresent the current catalog as a historical publication state.

```bash
.venv/bin/python scripts/plan_backfill.py --start-year 2010 --data-dir data --config-output data/plans/download.json --evidence-dir data/plans/evidence
.venv/bin/python -m usda_data fetch --dataset all --config data/plans/download.json --dry-run
.venv/bin/python -m usda_data fetch --dataset all --config data/plans/download.json
```

`--start-year` controls the starting scope; actual coverage still depends on the source and parser. Missing report catalog entries are recorded in the planning evidence; a missing entry does not prove that the report was never published.

## Aggregate seven final CSVs

A successful multi-task run first generates `data/exports/complete.latest.json`. The aggregation tool checks completion status, coverage of all seven datasets, input hashes, headers, and schema consistency before publishing the aggregate pointer:

```bash
.venv/bin/python scripts/aggregate_exports.py --input-dir data/exports --output-dir data/exports/datasets
.venv/bin/python -m usda_data validate --input-dir data/exports/datasets
```

Aggregation supports the RMA description migrations explicitly listed in `config/schema_migrations.json`; it does not convert business values. It no longer depends on old phase acceptance logs. A completed run and passing CSV validation do not replace independent audits of source values or automatically extend parser support to additional historical layouts.

## Historical data and evidence

The complete data from before the cleanup is in `downloading-usda-data-archive-20261117/original/data/` next to the repository; historical acceptance evidence is in `original/artifacts/` in the same archive. These directories are not used by default offline tests and are not automatically included in a new Git clone. See the [migration guide](repository_cleanup.md).
