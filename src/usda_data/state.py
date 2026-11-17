"""Versioned run and partition contracts; a check is distinct from publication."""
from dataclasses import asdict, dataclass, field
from typing import Literal
from .storage import atomic_write, canonical, safe_name, utc_now

@dataclass
class PartitionState:
    partition: str
    status: Literal["pending", "succeeded", "failed", "source_unavailable"] = "pending"
    snapshot_id: str | None = None
    watermark: str | None = None
    reason: str | None = None

@dataclass
class RunManifest:
    run_id: str
    dataset: str
    configuration_hash: str
    started_at_utc: str = field(default_factory=utc_now)
    schema_version: int = 1
    partitions: list[PartitionState] = field(default_factory=list)

    @property
    def complete(self):
        return bool(self.partitions) and all(p.status == "succeeded" and p.snapshot_id or p.status == "source_unavailable" and p.reason for p in self.partitions)

    def save(self, store):
        value = asdict(self)
        value["complete"] = bool(self.complete)
        from .security import sanitize
        atomic_write(store.root / "manifests" / "runs" / f"{safe_name(self.run_id)}.json", canonical(sanitize(value, store.secrets)))
