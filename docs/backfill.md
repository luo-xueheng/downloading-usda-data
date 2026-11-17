# Full backfill and acceptance

The full inventory is frozen in `config/full_backfill.json`. Its discovery cutoff is November 16, 2026; source receipts preserve the exact bytes acquired. The historical `config/datasets.toml` contains transport defaults, not the expanded 805-task inventory. Use the full configuration for backfill:

```bash
.venv/bin/python -m usda_data fetch --dataset all --config config/full_backfill.json --dry-run
.venv/bin/python -m usda_data fetch --dataset all --config config/full_backfill.json --resume
```

A successful task is not a passed phase. Phase 09 additionally requires source accounting, all report layouts, independent numeric audits, complete export linkage, resource measurement, and source-supported coverage gaps. The phase evidence directory is `artifacts/acceptance/phase-09/`.

## Safe recovery

Check for a still-running download before starting a second writer. Fetch/sync takes an operating-system lock for its data root. A second writer fails before changing run state; the lock is automatically released when the first process exits. Successful partitions and immutable raw archives survive failures. Resume checks existing export hashes and retries failed tasks. Never delete raw files or reset an incomplete run to claim completion.

The report backfill script checkpoints each attachment independently. It uses a fresh process per PDF to release parser and native-library memory. Default concurrency is one worker, within the configured 1 GiB (1,024 MiB) budget. It refuses to continue if parser source changes during the run. Cached receipts and resolved USDA NAL alternate attachments support an entirely offline replay:

```bash
.venv/bin/python scripts/backfill_reports.py --offline
```

A parser edit invalidates earlier report checks. Replaying with the new version preserves old normalized snapshots; stale hashes cannot satisfy acceptance. `--only-failed` is diagnostic and cannot pass the full gate while stale records remain.

After the report replay passes, resume the complete task run, then execute:

```bash
.venv/bin/python scripts/validate_backfill.py
.venv/bin/python scripts/reconcile_source_accounting.py
.venv/bin/python scripts/reconcile_backfill.py
.venv/bin/python scripts/audit_backfill.py
.venv/bin/python scripts/link_report_audits.py
.venv/bin/python scripts/check_backfill_resume.py
.venv/bin/python scripts/publish_backfill_exports.py
.venv/bin/python -m usda_data validate --input-dir data/exports/datasets
.venv/bin/python scripts/run_acceptance.py --phase 09 --mode offline
.venv/bin/python scripts/run_acceptance.py --phase 09 --mode live
```

The live suite makes bounded read-only official-source requests and uses an isolated data root. A missing or failing required check leaves the gate unpassed. `publish_backfill_exports.py` refuses to publish seven combined CSVs until the required tasks, validation and report checks succeed. `data/exports/datasets/complete.latest.json` selects the seven aggregate outputs; each records its exact component partition hashes and normalized snapshot IDs.

## Source meanings and limitations

WASDE structured files begin in April 2010. The requested January–March 2010 period is explicitly reported as unsupported by the implemented structured archive. ESR and PSD year identifiers are source marketing years, which can differ from the calendar years of the observation dates. RMA commodity-year 2027 and ERS forecast-year 2027 can already occur in files published by the November 2026 cutoff; their labels are not future retrieval dates.

A valid empty ESR API response is retained as evidence that the endpoint returned no observations at the cutoff. It is not a permanent-unavailability claim, and no zero-valued business rows are fabricated. Current-revised API observations never substitute for historical report vintages.

Some original report URLs serve a different month's PDF or return 404. Official USDA NAL alternatives are selected by their dated catalog entry and verified against the embedded PDF month. Original artifacts and access failures remain archived. Explicit nonpublication notices and exact-source missing-table records remain visible in coverage. WAP June 2016 Table 10 is absent from identical PDFs served by two official archives; that original table gap is not filled using adjacent months or today's API.

## Evidence freshness

`docs/execution_status.md` is the phase ledger. `summary.md`, `results.json`, `commands.txt`, and `source_checks.csv` in each phase directory describe verified work. During an active replay, an older `report_backfill_summary.json` remains evidence of the previous completed run; it must not be interpreted as the status of a newer incomplete run. Current per-file parser hashes, the active log, and the final summary must agree before closure.

## Memory budget revision — November 17, 2026

The user authorized increasing the Phase 09 full-backfill memory budget from 512 MiB to 1 GiB (1,024 MiB). This changes the resource acceptance threshold only; the frozen task inventory, source cutoff, numeric checks and output requirements remain the same. The completed seven-adapter export replay measured 689.5625 MiB and reproduced the original output hashes for every checked export. Its original 512 MiB failure and command exit code remain unchanged in `full_export_memory.json` and `bounded-full-export-replay.command.json`. `memory_budget_revision.json` records the reassessment under the new configuration. Formal acceptance compares measured peaks with the current configured budget. This evidence does not establish compatibility with 512 MiB environments.
