# Repository cleanup and migration on 2026-11-17

This cleanup separates download and processing code, tests, seven CSV examples, and documentation. No original data was permanently discarded; all 2,012 Git-tracked files were backed up before changes, and each SHA-256 hash was verified.

## Archive location

The local archive is next to the repository:

```text
../downloading-usda-data-archive-20261117/
├── archive_manifest.json   # Git HEAD, file sizes, and SHA-256 hashes before migration
├── data_migration.json     # Verification record for the complete data move
└── original/
    ├── data/              # Complete downloaded data, versions, source files, and runtime state
    ├── artifacts/         # Original phase acceptance records
    ├── output/            # Original network troubleshooting records
    ├── scripts/           # All scripts before migration
    ├── tests/             # Tests and fixtures before migration
    └── ...                # Other originally Git-tracked files
```

The complete data directory was moved with an atomic rename on the same filesystem. Relative paths, sizes, and inodes were checked for all 31,013 files, totaling approximately 34.87 GiB. The move reduced the amount of data inside the workspace but **did not free that disk space**. The archive still occupies disk space and is not automatically copied when the repository is pushed or cloned.

The local `.env`, `.venv`, and `.git` were not moved; credentials are not included in the archive.

## Current contents

- `src/` retains all download, parsing, versioned storage, synchronization, and CSV/SQL code, plus six JSON files required at runtime.
- `scripts/` retains general public-source acquisition, credential checks, task planning, aggregation, SQL transfer, and example-generation tools.
- `test/` centralizes tests, fixed fixtures, performance tools, and verification tools. Functional tests are organized by module/dataset, and generated outputs use temporary directories.
- `examples/` contains exactly seven CSVs with 200 rows each, along with download commands, excerpt rules, actual full-request row counts, and hashes.
- `config/` retains only runtime configuration, the frozen full-backfill configuration, a small-scope synchronization example, and schema migration rules.
- `schemas/` retains definitions for current interfaces and aggregate outputs. The direct RMA interface uses v2, and aggregation can migrate to v3; both are retained.
- All existing Markdown documents are retained; Markdown formerly in `artifacts/` has moved to `docs/history/acceptance/`. Historical copies of the original README and batch-download guide are stored separately.

165 remnants of failed downloads were removed from the test fixtures; their original bytes remain in the archive. Old logs, command records, monthly acceptance results, one-off phase-closing scripts, and network diagnostics are retained in the archive. Discovery pages and manifests actually required by tests were extracted into `test/fixtures/`.

Historical configurations and old schemas are retained in `docs/history/config/` and `docs/history/schemas/`. The PSD scope and report table inventories in the package are the maintained runtime sources; the old configuration copies are explicitly retained as historical records and no longer participate in execution.

## Finding and restoring files

The [complete file mapping](repository_migration_map.json) lists the current repository or external archive location of every file tracked by Git before migration. Historical acceptance paths in current documentation remain evidence identifiers for the original runs; do not treat historical logs as results of the current tests.

To restore a file, copy it from `original/` in the archive using its original relative path. When restoring a complete historical run, retain the raw files, normalized snapshots, exports, and manifests in `data/` together; copying only the final CSV cannot restore old checkpoints.

Current download tools accept `--data-dir` and `--output-dir`, so historical data does not need to be moved back into the repository. See the [testing guide](../test/README.md) for how to run historical delivery checks.

Example directories referenced by old documents but already missing before the cleanup were not fabricated. The new examples explicitly state that they come from offline replay of fixed official fixtures and do not claim to be freshly downloaded data.

## Verification results for this cleanup

- Default offline tests: 96 passed, with 25 live/historical acceptance tests excluded by configuration.
- Fixed-fixture replay for the seven primary datasets: full Python and CLI outputs matched field by field.
- Seven CSV examples: schema, row count, exact round-trip reading, and SHA-256 checks passed; report examples cover both source types.
- Aggregation tool: both RMA v2 migration and inputs already at v3 passed verification; corrupted inputs cannot replace the previous successful pointer.
- Installation: built a wheel offline, installed it in an isolated directory, and confirmed that the package and all required metadata load.
- All local Markdown links and 2,012 original file mappings resolve; all 39 original Markdown documents are retained.
- Download and parsing implementations in `src/` were unchanged. This cleanup did not redownload data online, rerun full historical performance checks, or treat historical acceptance results as current passing evidence.
