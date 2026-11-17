"""Strict, versioned, exact-value DataFrame and CSV contracts."""
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import csv
import io
import json
import pandas as pd
from .errors import ValidationError

NULL = "\\N"

@dataclass(frozen=True)
class Field:
    name: str
    type: str
    nullable: bool
    meaning: str
    source_mapping: str
    unit: str = "not_applicable"
    key: bool = False
    missing_rule: str = "Explicit null; zero remains zero; source markers retained separately"

@dataclass(frozen=True)
class Schema:
    name: str
    version: str
    fields: tuple[Field, ...]

    def __post_init__(self):
        names = [f.name for f in self.fields]
        if not self.version or len(names) != len(set(names)) or not names:
            raise ValidationError("Invalid schema identity/field names")
        if any(f.type not in {"string", "integer", "decimal", "date", "datetime", "boolean"} or not f.meaning or not f.source_mapping for f in self.fields):
            raise ValidationError("Incomplete or unsupported field contract")

    @property
    def names(self):
        return [f.name for f in self.fields]

    @property
    def keys(self):
        return [f.name for f in self.fields if f.key]

    def to_dict(self):
        return {"name": self.name, "version": self.version, "null_token": NULL, "escape": "Prefix literal backslash with another backslash", "fields": [asdict(f) for f in self.fields]}

    @classmethod
    def load(cls, path):
        obj = json.loads(Path(path).read_text())
        return cls(obj["name"], obj["version"], tuple(Field(**f) for f in obj["fields"]))

    def frame(self, records):
        records = list(records)
        if any(set(r) != set(self.names) for r in records):
            raise ValidationError("Unauthorized record field-layout change")
        return self.validate(pd.DataFrame(records, columns=self.names, dtype=object))

    def validate(self, frame):
        if list(frame.columns) != self.names:
            raise ValidationError("Unauthorized field-layout change")
        out = frame.copy().astype(object)
        for field in self.fields:
            out[field.name] = pd.Series([convert(v, field) for v in out[field.name]], index=out.index, dtype=object)
        if self.keys and out.duplicated(self.keys).any():
            raise ValidationError("Duplicate business keys")
        return out

    def csv_bytes(self, frame):
        frame = self.validate(frame)
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(self.names)
        for row in frame.itertuples(index=False, name=None):
            writer.writerow([encode(v) for v in row])
        return stream.getvalue().encode("utf-8")

    def read_csv(self, path):
        with Path(path).open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            if next(reader, None) != self.names:
                raise ValidationError("CSV field-layout change")
            records = []
            for row in reader:
                if len(row) != len(self.fields):
                    raise ValidationError("CSV row width mismatch")
                records.append({f.name: decode(v, f) for f, v in zip(self.fields, row)})
        return self.frame(records)

    def read_csv_chunks(self, path, chunk_size=5000):
        """Read exact typed CSV chunks without materializing a complete partition."""
        if type(chunk_size) is not int or chunk_size < 1:
            raise ValidationError("Chunk size must be a positive integer")
        with Path(path).open(encoding="utf-8", newline="") as stream:
            reader=csv.reader(stream,strict=True)
            if next(reader,None)!=self.names:raise ValidationError("CSV field-layout change")
            records=[]
            for row in reader:
                if len(row)!=len(self.fields):raise ValidationError("CSV row width mismatch")
                records.append({f.name:decode(v,f) for f,v in zip(self.fields,row)})
                if len(records)==chunk_size:
                    yield self.frame(records);records=[]
            if records:yield self.frame(records)

    def write_csv(self, frame, path):
        from .storage import atomic_write
        atomic_write(Path(path), self.csv_bytes(frame))

def is_null(value):
    return value is None or value is pd.NA or value is pd.NaT

def convert(value, field):
    if is_null(value):
        if not field.nullable or field.key:
            raise ValidationError(f"Missing required dimension: {field.name}")
        return None
    valid = {
        "string": lambda v: isinstance(v, str),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "decimal": lambda v: isinstance(v, Decimal) and v.is_finite(),
        "date": lambda v: isinstance(v, date) and not isinstance(v, datetime),
        "datetime": lambda v: isinstance(v, datetime) and v.tzinfo is not None and v.utcoffset().total_seconds() == 0,
        "boolean": lambda v: isinstance(v, bool),
    }[field.type](value)
    if not valid or (field.key and value == ""):
        raise ValidationError(f"Invalid {field.type} value: {field.name}")
    return value

def encode(value):
    if is_null(value):
        return NULL
    text = value.isoformat() if isinstance(value, (date, datetime)) else str(value)
    return "\\" + text if text.startswith("\\") else text

def decode(text, field):
    if text == NULL:
        return None
    if text.startswith("\\\\"):
        text = text[1:]
    try:
        if field.type == "string":
            return text
        if field.type == "integer":
            return int(text)
        if field.type == "decimal":
            return Decimal(text)
        if field.type == "date":
            return date.fromisoformat(text)
        if field.type == "datetime":
            return datetime.fromisoformat(text)
        if field.type == "boolean" and text in {"True", "False"}:
            return text == "True"
    except (ValueError, InvalidOperation):
        pass
    raise ValidationError(f"Invalid CSV value in {field.name}")
