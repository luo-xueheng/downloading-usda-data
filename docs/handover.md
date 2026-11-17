# Handover and original requirement checklist

The package, source evidence and selected data are delivered locally. No production
service, database deployment or actual scheduler is part of this release.

| Original internship requirement | Delivered implementation and evidence |
|---|---|
| Understand release timing | `docs/release_notes.md`, `config/calendar.json`, `docs/source_registry.md`; Phase 00/08 and final live evidence preserve precision and unknown synchronization. |
| Prefer APIs | Authenticated ESR and PSD adapters, with official structured files for WASDE/ERS/RMA; Phases 04/05 and Phase 10 live suites. |
| Explain economic meaning | Seven dataset guides, `docs/field_dictionary.md`, exact units, source dimensions, aggregate and vintage caveats. |
| Public Python functions | `src/usda_data/api.py`; seven real-fixture Python/CLI comparisons, plus PSD and report-archive interfaces. |
| Unified CLI | `src/usda_data/cli.py`; help, calendar, fetch, sync, validate and exit-code regression coverage. |
| Modular implementation | Shared HTTP/storage/schema/state/calendar modules and independent `sources/` adapters; no production parser changed for handover. |
| SQL-ready delivery | Fixed CSV/schema sidecars; exact-decimal SQLite transfer, all full rows hashed after readback, native business-key/required-field constraints. |
| Full requested historical scope | Seven complete exports, 805 source tasks, 606 attachment candidates, 164 independent numeric checks and zero unresolved required coverage records in Phase 09. |
| Reproducibility and later updates | Raw receipts, immutable normalized snapshots, source-tree/config hashes, clean wheel installation, explicit sync and recovery procedures. |

Start from `data/exports/datasets/complete.latest.json`. Transfer that manifest and
all referenced CSV/schema files together; retain `data/raw`, `data/normalized`,
`data/reports` and `data/manifests` for reproducibility and refresh. Paths in the
manifest are relative to `data/exports/datasets`. The Phase 10 final manifest is
an exact copy of the accepted selection, not a new backfill or a latest-data claim.

Installation and examples are in README. CSV and SQL handling are in
`docs/sql_transfer.md`; operator recovery is in `docs/updates_and_recovery.md`.
Use the full task inventory rather than the small development examples for a full
refresh. Back up the complete manifest before moving data; do not delete old raw
versions. Credentials must be configured locally and are excluded from delivery.

`docs/acceptance_index.md` links every acceptance phase. Required live evidence is
separate from deterministic offline replay. A passing snapshot of evidence says
what succeeded at its recorded time; it does not assert ongoing endpoint uptime.
Source gaps and unknown precise availability times remain documented limitations,
not hidden implementation defects.
