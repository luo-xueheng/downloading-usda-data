"""Environment-first FAS key loading; never execute .env contents or log values."""
import os
from pathlib import Path

DEFAULT_ENV_FILE = Path('.env')
KEY_NAME = 'USDA_FAS_API_KEY'


def load_api_key(env_file=None):
    """Return the key, preferring a nonempty process environment variable.

Otherwise read USDA_FAS_API_KEY from the explicit path or repository-root .env.
A file value is also exported into this Python process's environment. Existing
shells and unrelated processes are not modified. Errors never include values.
Supported file syntax: blank lines, full-line comments, NAME=value, optional
matching single/double quotes, and an optional leading 'export '. Other settings
are ignored. Duplicate key assignments and multiline values are rejected.
"""
    existing = os.environ.get(KEY_NAME, '').strip()
    if existing:
        return _validate(existing)
    target = Path(env_file) if env_file is not None else DEFAULT_ENV_FILE
    if not target.is_file():
        raise ValueError('No API key configured. Set USDA_FAS_API_KEY in the project .env file.')
    value = None
    for line in target.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[7:].lstrip()
        name, separator, raw = line.partition('=')
        if name.strip() != KEY_NAME:
            continue
        if not separator or value is not None:
            raise ValueError('Malformed or duplicate USDA_FAS_API_KEY assignment in .env.')
        raw = raw.strip()
        if raw.startswith(('"', "'")):
            if len(raw) < 2 or raw[-1] != raw[0]:
                raise ValueError('USDA_FAS_API_KEY quotes must match on one line.')
            raw = raw[1:-1]
        value = _validate(raw)
    if value is None:
        raise ValueError('The .env file must contain USDA_FAS_API_KEY=your_key on one line.')
    os.environ[KEY_NAME] = value
    return value


def _validate(value):
    if not value or any(c.isspace() or ord(c) < 33 or ord(c) > 126 for c in value):
        raise ValueError('USDA_FAS_API_KEY must be a nonempty single-line value without whitespace.')
    return value

