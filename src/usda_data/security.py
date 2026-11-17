"""Redact authentication before persistent logging or exception construction."""
import re
from urllib.parse import urlsplit, urlunsplit

SENSITIVE = re.compile(r"api[-_]?key|authorization|token|secret|password|credential", re.I)

def safe_url(url):
    """Omit userinfo, query and fragment, which can contain source credentials."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc.rsplit("@", 1)[-1], parts.path, "", ""))

def sanitize(value, secrets=()):
    if isinstance(value, dict):
        return {str(k): "[REDACTED]" if SENSITIVE.search(str(k)) else sanitize(v, secrets) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(v, secrets) for v in value]
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        if value.startswith(("https://", "http://")):
            value = safe_url(value)
    return value
