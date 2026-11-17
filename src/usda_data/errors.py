"""Public failure categories. Exceptions must never contain credentials."""
class USDAError(Exception):
    """Base runtime failure."""

class ConfigurationError(USDAError, ValueError):
    """Invalid request or configuration."""

class AuthenticationError(USDAError):
    """Missing or rejected source access."""

class DownloadError(USDAError):
    """Transport failure after finite retries."""

class FormatError(USDAError):
    """Unexpected source format or layout."""

class ValidationError(USDAError, ValueError):
    """Invalid dimensions, keys, or values."""

class PendingRelease(USDAError):
    """A configured source artifact is not yet available for its saved release event."""
