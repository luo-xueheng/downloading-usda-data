# Updates, calendars and recovery

Run `python -m usda_data sync --dataset all --config config/small_sync.json` for the
explicit small acceptance configuration. It is not the full backfill configuration.
Every task has its own dataset-specific range/options. `fetch --dataset all --config
PATH --dry-run` prints the frozen task inventory without numeric downloads; source
metadata discovery is a separate planning step. No scheduler is installed.

`sync` rechecks all configured partitions, including older years. Source responses
at unchanged URLs are refetched and byte hashes compared. Identical captures reuse
normalized snapshots while each check remains logged. FAS dictionaries/commodity
partitions shared by report families are fetched once within one refresh operation.
Revised complete files/partitions replace the latest view, retaining old raw bytes
and normalized snapshots. Added, changed and deleted source rows are all reflected.

Run state is saved after each transition under data/manifests/runs. Each task records
attempts, status, successful watermark and the exact export hash/schema/partition
references. Data preparation happens in exports/runs/RUN_ID/TASK_ID. The authoritative
complete.latest.json pointer changes only after every required task succeeds.
A runtime, validation or pending-release failure yields partial status and exit 1;
the preceding complete export remains selected. A failed task's watermark is null.
Internal prepared artifacts can exist after failure but are not a complete run.

Resume with `sync --dataset all --config PATH --resume`. The configuration/task hash
must match. Completed task outputs are hash-checked and reused; failed or corrupted
tasks are rerun. A crash before final manifest selection can resume directly to
publication after confirming successful tasks. Repeated successful unchanged checks
still create a run/attempt record but no redundant source-normalized snapshot.
Change the explicit configuration only for a new run, not an incompatible resume.

Run `python -m usda_data validate --input-dir EXPORT_ROOT` to verify selected CSV
hashes, row counts, exact typed schemas and complete business-key uniqueness using
a disk-backed key index. Do this before consuming a published export. The manifest
and its CSV/schema references, rather than arbitrary temporary files, define the
selected output.

The saved calendar is config/calendar.json. It includes source evidence URLs,
verification timestamps, artifact kinds, precision and explicit events. Read it with
`python -m usda_data calendar --dataset all`. Known source clocks are converted using
the source timezone (America/New_York where verified), then stored as UTC. Asia/Shanghai
is a display option, not source metadata. A date-only event yields no fabricated
clock or UTC instant. Old event verification is labeled stale; no stale calendar
is represented as confirmed fresh.

Availability is per artifact: an API partition may be available while its report
remains pending. Saved holiday-shifted events determine expected dates; there is
no hard-coded weekday substitute. Delayed, date-only pending and stale-calendar
states remain distinct. Unknown freshness is never a confirmation of current data.
The source registry's publication claims preserve verified versus unverified rules.
A future calendar update must retain its official evidence and not infer actual
availability from a scheduled time alone.

Recovery procedure:

1. Read the last run's task statuses and error types; no authentication values or
   arbitrary upstream exception bodies are persisted.
2. Restore source access or correct the explicit configuration/layout defect.
3. Resume the same run with unchanged configuration. Successful prepared tasks are
   verified before reuse; failures never advance their watermarks.
4. Validate the selected complete export and inspect coverage before downstream use.

For optional scheduling, an operator may run the documented sync command from their
chosen scheduler after reviewed official release events, including a retry for delayed
artifacts. This package does not install cron, launchd, services or recurring jobs.
