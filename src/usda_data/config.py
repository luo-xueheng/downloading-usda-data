"""Validated immutable runtime configuration; source scope lives in config/."""
from dataclasses import dataclass
from pathlib import Path
import tomllib
from .errors import ConfigurationError

DATASETS = ("wasde", "export-sales", "world-production", "grain-trade", "oilseed-trade", "costs-returns", "rma-sob")

@dataclass(frozen=True)
class HTTPConfig:
    trust_environment: bool = True
    timeout_seconds: float = 30.0
    max_attempts: int = 3
    backoff_seconds: float = 0.5
    max_retry_delay: float = 30.0
    max_response_bytes: int = 100_000_000

    def __post_init__(self):
        if not isinstance(self.trust_environment, bool):
            raise ConfigurationError("trust_environment must be boolean")
        if self.timeout_seconds <= 0 or self.max_attempts < 1 or self.max_response_bytes < 1 or min(self.backoff_seconds, self.max_retry_delay) < 0:
            raise ConfigurationError("Timeout/attempt/byte limits must be positive; delays nonnegative")

    @classmethod
    def from_file(cls, path):
        values = tomllib.loads(Path(path).read_text()).get("http", {})
        try:
            return cls(**values)
        except TypeError:
            raise ConfigurationError("Unknown HTTP configuration field") from None
