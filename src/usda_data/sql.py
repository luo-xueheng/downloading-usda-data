"""Lossless local SQLite transfer with explicit business-key constraints.

Decimal values use TEXT (never REAL/NUMERIC affinity), retaining every source
 digit. Decimal key comparisons use a registered exact Decimal collation.
"""
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import sqlite3
from pathlib import Path

from .errors import ValidationError
from .schema import Schema, convert, decode, encode


def quote(name):
    return '"' + name.replace('"', '""') + '"'


def connect(path):
    """Open a local database and register exact-decimal key comparisons."""
    db = sqlite3.connect(path)
    db.create_collation('exact_decimal', lambda a, b: (Decimal(a) > Decimal(b)) - (Decimal(a) < Decimal(b)))
    def finite(value):
        try:
            return isinstance(value, str) and Decimal(value).is_finite()
        except (InvalidOperation, ValueError):
            return False
    db.create_function('finite_decimal', 1, finite, deterministic=True)
    return db


def create_table(db, table, schema):
    """Create typed columns and a composite UNIQUE key over real dimensions."""
    if not schema.keys:
        raise ValidationError('Business SQL tables require declared business keys')
    definitions = []
    for field in schema.fields:
        name = quote(field.name)
        kind = 'INTEGER' if field.type in {'integer', 'boolean'} else 'TEXT'
        parts = [name, kind]
        if field.key or not field.nullable:
            parts.append('NOT NULL')
        if field.type == 'decimal':
            parts.append('COLLATE exact_decimal')
            check = f"typeof({name}) = 'text' AND finite_decimal({name})"
        else:
            check = f"typeof({name}) = '{kind.lower()}'"
        if field.key and kind == 'TEXT':
            check += f" AND length({name}) > 0"
        if field.type == 'boolean':
            check += f' AND {name} IN (0, 1)'
        parts.append(f'CHECK ({name} IS NULL OR ({check}))')
        definitions.append(' '.join(parts))
    definitions.append('UNIQUE (' + ', '.join(map(quote, schema.keys)) + ')')
    db.execute(f'CREATE TABLE {quote(table)} (' + ', '.join(definitions) + ')')


def sql_value(value, field):
    if value is None:
        return None
    if field.type in {'integer', 'boolean'}:
        return int(value)
    if field.type in {'date', 'datetime'}:
        return value.isoformat()
    return str(value)


def insert_sql(table, schema):
    return f'INSERT INTO {quote(table)} (' + ','.join(map(quote, schema.names)) + ') VALUES (' + ','.join('?' for _ in schema.fields) + ')'


def import_csv(db, table, schema, path, *, chunk_size=5000):
    """Validate and stream a complete CSV into a new table in one transaction.

    Failure rolls back the table and its rows. Existing tables are never replaced.
    """
    if type(chunk_size) is not int or chunk_size < 1:
        raise ValidationError('Chunk size must be a positive integer')
    db.execute('SAVEPOINT usda_import')
    try:
        create_table(db, table, schema)
        statement = insert_sql(table, schema)
        count = 0
        with Path(path).open(encoding='utf-8', newline='') as stream:
            reader = csv.reader(stream, strict=True)
            if next(reader, None) != schema.names:
                raise ValidationError('CSV field-layout change')
            batch = []
            for row in reader:
                if len(row) != len(schema.fields):
                    raise ValidationError('CSV row width mismatch')
                batch.append(tuple(sql_value(convert(decode(v, f), f), f) for v, f in zip(row, schema.fields)))
                if len(batch) >= chunk_size:
                    db.executemany(statement, batch)
                    count += len(batch)
                    batch = []
            if batch:
                db.executemany(statement, batch)
                count += len(batch)
        db.execute('RELEASE usda_import')
        return count
    except Exception:
        db.execute('ROLLBACK TO usda_import')
        db.execute('RELEASE usda_import')
        raise


def readback_hash(db, table, schema, *, chunk_size=5000):
    """Re-encode every SQL row as contract CSV, checking nulls and exact values."""
    digest = hashlib.sha256()
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow(schema.names)
    digest.update(stream.getvalue().encode('utf-8'))
    cursor = db.execute('SELECT ' + ','.join(map(quote, schema.names)) + f' FROM {quote(table)} ORDER BY rowid')
    count = 0
    while rows := cursor.fetchmany(chunk_size):
        stream.seek(0)
        stream.truncate(0)
        for row in rows:
            # TEXT stores unescaped source strings, ISO dates and exact decimals;
            # CSV escaping is reapplied here. INTEGER booleans need their lexeme.
            writer.writerow([encode(bool(v) if f.type == 'boolean' and v is not None else v) for v, f in zip(row, schema.fields)])
        digest.update(stream.getvalue().encode('utf-8'))
        count += len(rows)
    return {'rows': count, 'csv_sha256': digest.hexdigest()}


def check_constraints(db, table, schema):
    """Prove duplicates and each missing required field fail at the SQL boundary."""
    row = db.execute(f'SELECT * FROM {quote(table)} LIMIT 1').fetchone()
    if row is None:
        raise ValidationError('Constraint proof requires a nonempty source sample')
    statement = insert_sql(table, schema)
    def rejected(values, expected):
        db.execute('SAVEPOINT constraint_probe')
        try:
            db.execute(statement, values)
        except sqlite3.IntegrityError as exc:
            if expected not in str(exc):
                raise ValidationError('Unexpected SQL constraint failure') from None
        else:
            raise ValidationError('SQL accepted an invalid row')
        finally:
            db.execute('ROLLBACK TO constraint_probe')
            db.execute('RELEASE constraint_probe')
    rejected(row, 'UNIQUE constraint failed')
    fields = []
    for index, field in enumerate(schema.fields):
        if field.key or not field.nullable:
            changed = list(row)
            changed[index] = None
            rejected(changed, 'NOT NULL constraint failed')
            fields.append(field.name)
        if field.key and field.type == 'decimal':
            changed = list(row)
            changed[index] = str(Decimal(row[index])) + ('0' if '.' in row[index] else '.0')
            rejected(changed, 'UNIQUE constraint failed')
    return {'duplicate_rejected': True, 'missing_fields_rejected': fields}
