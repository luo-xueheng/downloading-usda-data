# Acceptance evidence index

The execution ledger is the authoritative phase status. Historical phase results retain their original source-tree/configuration identities. Final suites re-exercise the mandatory tests at handover; they do not rewrite past acceptance hashes.

| Phase | Evidence | Machine-readable results |
|---|---|---|
| 00 | [Summary](../artifacts/acceptance/phase-00/summary.md) | [Results](../artifacts/acceptance/phase-00/results.json) |
| 01 | [Summary](../artifacts/acceptance/phase-01/summary.md) | [Results](../artifacts/acceptance/phase-01/results.json) |
| 02 | [Summary](../artifacts/acceptance/phase-02/summary.md) | [Results](../artifacts/acceptance/phase-02/results.json) |
| 03 | [Summary](../artifacts/acceptance/phase-03/summary.md) | [Results](../artifacts/acceptance/phase-03/results.json) |
| 04 | [Summary](../artifacts/acceptance/phase-04/summary.md) | [Results](../artifacts/acceptance/phase-04/results.json) |
| 05 | [Summary](../artifacts/acceptance/phase-05/summary.md) | [Results](../artifacts/acceptance/phase-05/results.json) |
| 06 | [Summary](../artifacts/acceptance/phase-06/summary.md) | [Results](../artifacts/acceptance/phase-06/results.json) |
| 07 | [Summary](../artifacts/acceptance/phase-07/summary.md) | [Results](../artifacts/acceptance/phase-07/results.json) |
| 08 | [Summary](../artifacts/acceptance/phase-08/summary.md) | [Results](../artifacts/acceptance/phase-08/results.json) |
| 09 | [Summary](../artifacts/acceptance/phase-09/summary.md) | [Results](../artifacts/acceptance/phase-09/results.json) |
| 10 | [Summary](../artifacts/acceptance/phase-10/summary.md) | [Results](../artifacts/acceptance/phase-10/results.json) |

## Final handover evidence

- `artifacts/acceptance/phase-10/commands.txt`: exact invocations, working directory and exit codes.
- `clean_environment.json`, `clean-install.txt`, `final-wheel-install.txt`, `requirements-tested.txt`: isolated wheel installation and resolved dependency versions.
- `examples/checks.json`: seven installed Python/CLI comparisons, with command arguments and hashes.
- `sql_roundtrip.json`: all complete rows, source/export hashes, schema hashes and SQL constraint rejection checks.
- `required-live.xml` and `required-live.txt`: all nine required adapter live tests, with no skipped tests.
- `phase-00/` and `phase-00-direct/`: independent standard-library inventory, public access and reference verifier.
- `all-offline.xml`: complete final offline suite, including Phase 10.
- `final_dataset_manifest.json` and `handover_index.json`: selected data and documentation coverage.
- `source_checks.csv`: explicit reference to existing independent numeric accuracy evidence; no new numerical truth is inferred from roundtrip equality.

The initial SQL constraint failure and RMA HTTP 502 probes are retained separately. Later passing evidence must actually rerun the affected checks. No failed or skipped run is counted as a pass.
