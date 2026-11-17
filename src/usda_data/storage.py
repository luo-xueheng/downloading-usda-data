"""Content-addressed immutable artifacts and atomic publication pointers."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from .errors import ValidationError
from .security import sanitize

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def atomic_write(path, data, *, before_replace=None):
    """Flush a sibling temporary file then replace; clean up on any failure."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if before_replace:
            before_replace()
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)

def safe_name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value):
        raise ValidationError("Invalid partition/dataset identifier")
    return value

class Store:
    def __init__(self, root="data", *, secrets=()):
        self.root = Path(root)
        self.secrets = tuple(secrets)

    def raw(self, body, *, metadata):
        artifact_id = sha256(body)
        path = self.root / "raw" / artifact_id[:2] / artifact_id
        if path.exists():
            if hash_file(path) != artifact_id:
                raise ValidationError("Corrupted existing raw artifact")
        else:
            atomic_write(path, body)
        record = sanitize({**metadata, "source_artifact_id": artifact_id, "bytes": len(body), "retrieved_at_utc": utc_now()}, self.secrets)
        receipt_id = sha256(canonical(record))
        atomic_write(self.root / "manifests" / "acquisitions" / f"{receipt_id}.json", canonical(record))
        return record

    def artifact(self, artifact_id):
        if not re.fullmatch("[a-f0-9]{64}", artifact_id):
            raise ValidationError("Invalid artifact identity")
        path = self.root / "raw" / artifact_id[:2] / artifact_id
        if hash_file(path) != artifact_id:
            raise ValidationError("Artifact hash mismatch")
        return path

    def publish(self, dataset, partition, frame, schema, artifact_ids, *, parser_version, configuration, before_publish=None):
        """Write immutable snapshot files; latest changes only after validation succeeds.

        Concurrent callers may each publish a complete version; the last atomic
        pointer replacement wins. Cross-partition run selection belongs to sync.
        """
        dataset, partition = safe_name(dataset), safe_name(partition)
        for artifact_id in artifact_ids:
            self.artifact(artifact_id)
        if not artifact_ids or not parser_version:
            raise ValidationError("Snapshot requires source artifacts and parser version")
        identity = {"dataset": dataset, "partition": partition, "source_artifact_ids": sorted(set(artifact_ids)), "parser_version": parser_version, "schema": schema.to_dict(), "configuration": sanitize(configuration, self.secrets)}
        snapshot_id = sha256(canonical(identity))
        frame = frame.copy()
        if "snapshot_id" in frame:
            frame["snapshot_id"] = snapshot_id
        if schema.keys:
            frame = frame.sort_values(schema.keys, kind="stable").reset_index(drop=True)
        body = schema.csv_bytes(frame)
        folder = self.root / "normalized" / dataset / partition / snapshot_id
        manifest = {**identity, "snapshot_id": snapshot_id, "csv_sha256": sha256(body), "rows": len(frame), "csv_path": str((folder / "data.csv").relative_to(self.root))}
        if folder.exists() and (folder / "manifest.json").exists():
            existing = json.loads((folder / "manifest.json").read_text())
            if existing["csv_sha256"] != manifest["csv_sha256"]:
                # Same inputs/version must produce identical output, including provenance.
                raise ValidationError("Nondeterministic snapshot output; increment parser/config version")
            if sha256((folder / "data.csv").read_bytes()) != existing["csv_sha256"]:
                raise ValidationError("Corrupted existing normalized snapshot")
        else:
            atomic_write(folder / "data.csv", body)
            atomic_write(folder / "manifest.json", canonical(manifest))
        atomic_write(self.root / "manifests" / dataset / f"{partition}.latest.json", canonical(manifest), before_replace=before_publish)
        return manifest

    def latest(self, dataset, partition):
        path = self.root / "manifests" / safe_name(dataset) / f"{safe_name(partition)}.latest.json"
        if not path.exists():
            return None
        manifest = json.loads(path.read_text())
        csv_path = (self.root / manifest["csv_path"]).resolve()
        if not csv_path.is_relative_to(self.root.resolve()) or hash_file(csv_path) != manifest["csv_sha256"]:
            raise ValidationError("Published snapshot integrity failure")
        return manifest

    def publish_stream(self, dataset, partition, frames, schema, artifact_ids, *, parser_version, configuration, before_publish=None):
        """Publish a large partition with disk-backed full-key uniqueness checks.

        Input/source order is retained. Chunk size is not part of data identity;
        different chunk boundaries must produce identical bytes. Complete immutable
        files are selected only after all chunks and cross-chunk keys validate.
        """
        import sqlite3
        from decimal import Decimal
        dataset,partition=safe_name(dataset),safe_name(partition)
        for artifact_id in artifact_ids:self.artifact(artifact_id)
        if not artifact_ids or not parser_version:raise ValidationError('Missing streaming snapshot provenance')
        identity={'dataset':dataset,'partition':partition,'source_artifact_ids':sorted(set(artifact_ids)),'parser_version':parser_version,'schema':schema.to_dict(),'configuration':sanitize(configuration,self.secrets)}
        snapshot_id=sha256(canonical(identity));staging=self.root/'normalized'/dataset/partition;staging.mkdir(parents=True,exist_ok=True)
        fd,pending=tempfile.mkstemp(prefix='.pending-',dir=staging)
        key_fd,key_path=tempfile.mkstemp(prefix='.keys-',suffix='.sqlite',dir=staging);os.close(key_fd)
        database=sqlite3.connect(key_path);database.execute('CREATE TABLE business_keys (dimensions TEXT PRIMARY KEY)')
        rows=0;digest=hashlib.sha256()
        try:
            with os.fdopen(fd,'wb') as stream:
                header=schema.csv_bytes(schema.frame([]));stream.write(header);digest.update(header)
                for frame in frames:
                    frame=frame.copy()
                    if 'snapshot_id' in frame:frame['snapshot_id']=snapshot_id
                    frame=schema.validate(frame)
                    if schema.keys:
                        values=[(json.dumps([str(v.normalize()) if isinstance(v,Decimal) else str(v) for v in row],ensure_ascii=False,separators=(',',':')),) for row in frame[schema.keys].itertuples(index=False,name=None)]
                        try:database.executemany('INSERT INTO business_keys VALUES (?)',values)
                        except sqlite3.IntegrityError:raise ValidationError('Duplicate business key across streaming chunks') from None
                        database.commit()
                    body=schema.csv_bytes(frame).split(b'\n',1)[1];stream.write(body);digest.update(body);rows+=len(frame)
                stream.flush();os.fsync(stream.fileno())
            folder=staging/snapshot_id;folder.mkdir(parents=True,exist_ok=True)
            manifest={**identity,'snapshot_id':snapshot_id,'csv_sha256':digest.hexdigest(),'rows':rows,'csv_path':str((folder/'data.csv').relative_to(self.root))}
            if (folder/'manifest.json').exists():
                old=json.loads((folder/'manifest.json').read_text())
                if old['csv_sha256']!=manifest['csv_sha256']:raise ValidationError('Nondeterministic streaming snapshot output')
                if hash_file(folder/'data.csv')!=manifest['csv_sha256']:raise ValidationError('Corrupted streaming snapshot')
            else:
                os.replace(pending,folder/'data.csv');atomic_write(folder/'manifest.json',canonical(manifest))
            atomic_write(self.root/'manifests'/dataset/f'{partition}.latest.json',canonical(manifest),before_replace=before_publish)
            return manifest
        finally:
            database.close();Path(pending).unlink(missing_ok=True);Path(key_path).unlink(missing_ok=True)


def hash_file(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()
