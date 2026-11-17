# Phase 08 acceptance report

Phase: 08 — Revision handling, release calendars and recovery  
Status: **passed**  
Completed UTC: 2026-11-16T05:06:05.529455+00:00  
Configuration hash: `27f0de7c999737619803fe670ccb257cf53bbb2a9a827507c6aee87067ef2c51`  
Git revision: `726fa52aab88f187fd28d742277b918a26821785`  
Source-tree hash: `367551d5a141fc53971f47faf8508a9aa6a488330c0f9559bf47686da555a518`

## Implemented behavior and acceptance

Persisted source task/run state, all-configured historical refresh policy,
complete-run atomic export selection, resumable failed/partial jobs, unchanged
check logging, shared FAS refresh-request reuse, explicit pending report status,
evidence-backed publication events/precision/timezones/staleness, sync/dry-run/
calendar/validate CLI commands and docs/updates_and_recovery.md.

P08-A1 through P08-A9: **9 passed / 0 failed / 0 blocked**.
Eleven offline test cases plus one mandatory live case pass with final matching
code/config hashes. Live: A9; offline: A1-A8. All source-accuracy tests remain
separate from explicitly synthetic revision/failure/clock fixtures.

Version B adds, changes and removes rows; latest equals B exactly while A remains
reproducible. An unchanged source URL with an older-year revision is refetched.
Unchanged successful checks create new attempt logs without redundant normalized
snapshots. Injected failures before download, after normalization and before final
manifest publication preserve the preceding complete selected export. Failed tasks
have no advanced watermark. Resume reuses only hash-verified successful tasks and
produces the same canonical output as a clean run. One failed required partition
makes the run partial/nonzero; no partial complete-run pointer is published.

Fixed-clock timezone cases convert January 15, 2026 noon America/New_York to
17:00 UTC and July 15 noon to 16:00 UTC. These are timezone tests, not USDA release
dates. Date-only events produce no invented timestamp. An explicitly saved shifted
holiday event controls pending/delayed state; stale calendars remain labeled stale.
API availability and pending report status remain separate. Unknown freshness is
never represented as confirmed current.

The authenticated live ESR update check succeeds twice; the second reports unchanged
and both runs remain logged. Unavailable-source behavior uses finite attempt limits
and explicit failure. All seven datasets also complete a real isolated sync with
separate source ranges and frozen small-sample selections. The selected complete
run is 20261116T040806-57eba300; validation.json confirms seven export hashes, row counts,
schema types and complete keys. This is integration acceptance, not full backfill.

## Evidence and limitations

Commands/exit codes: commands.txt. Synthetic test node results: test_cases.offline.json.
Real update evidence: live/checks.json. Real seven-dataset run: small_sync_result.json
and sample/data/manifests/runs/. Complete export selector: sample/exports/
complete.latest.json. Schema/key/hash validation: validation.json. Calendar source
claims/events: config/calendar.json; display output: calendar_output.json. Dry-run
inventory: dry_run.json. Recovery and optional operator scheduling instructions:
docs/updates_and_recovery.md. No recurring scheduler/service has been installed.

Only explicitly saved events assert calendar dates/times; report, API and historical
file claims remain separate. Dynamic future calendars still require verified source
updates, and an empty source response does not itself establish permanent absence.
Full frozen-scope inventory, storage estimation, backfill, gap reconciliation and
140 additional independent audit cells are mandatory Phase 09 work.

Implementation defects open for required Phase 08: none.  
External blockers: none.  
Next eligible phase: 09 — freeze the full available-partition inventory and cutoff,
estimate storage/request counts, run complete configured backfill and reconcile all
required partitions and additional independent audits before handover.
