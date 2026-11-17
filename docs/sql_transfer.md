# Exact CSV and local SQL transfer

> Repository cleanup (2026-11-17): historical `artifacts/` and full `data/` paths below refer to the external archive. See [migration and archive guide](repository_cleanup.md). These saved results are not current test results.


Run from the repository after installation, selecting a **new** database path:

```bash
.venv/bin/python scripts/sql_roundtrip.py --input-dir data/exports/datasets --database artifacts/acceptance/phase-10/sql/verified.sqlite --output artifacts/acceptance/phase-10/sql_roundtrip.json
```

The command reads the selected complete manifest, verifies each source CSV hash,
streams every row through an isolated local SQLite database, and re-encodes every
SQL value to CSV. Counts and SHA-256 must equal the original full CSV, including
column order, leading-zero codes, ISO dates, null markers and decimal lexemes.
Existing database files are rejected; choose another path when repeating it.
It does not connect to a production database. Import is atomic per dataset.

Decimal columns have **TEXT affinity**, with finite-decimal validation; no float
or SQLite NUMERIC affinity conversion occurs. This supports varying source scales
without a lossy common multiplier. Read values using Python `Decimal`. SQL native
`SUM`, `AVG` and numeric casts are not exact-decimal analysis; calculate in Decimal
or migrate into a database with an appropriate exact NUMERIC/DECIMAL type after
checking precision/scale. Integer and boolean fields use INTEGER, strings and
ISO date/timestamps use TEXT. Null is SQL NULL. Literal `\N`, empty string and null
stay distinct through the CSV backslash escaping contract in `Schema`.

Each table has a composite UNIQUE constraint over the declared business dimensions,
NOT NULL on every key and required field, and typed-value checks. Decimal keys use
a registered `exact_decimal` collation so `0.50` and `0.500` cannot bypass uniqueness.
Reopen these databases using `usda_data.sql.connect` before writing; it registers
the collation and decimal validator. Plain SQLite clients can inspect most fields
but cannot perform writes requiring those functions/collations. No hash substitutes
for the original dimensions. Import validation also checks source date formats.

The verifier deliberately inserts duplicates and independently removes **each**
required field, requiring SQL rejection. Additional synthetic regression tests
cover values above binary float precision, negative zero, nulls, escaped strings,
equivalent decimal keys and rollback of a duplicate found in a later chunk.
Synthetic cases are supplementary; the full official exports supply the transfer
acceptance evidence. Memory is bounded by the chunk size and database cache.

Machine-readable field types, meanings, source mappings, null rules and key flags
are in each export's `schema.json`. A human-readable current inventory is in
[field_dictionary.md](field_dictionary.md). Use `Schema.read_csv_chunks` rather
than pandas automatic type inference for exact roundtrip handling.
