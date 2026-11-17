#!/usr/bin/env python3
"""Load the FAS API key from the environment or a local .env file.

This deliberately supports one setting, not shell syntax or general dotenv
interpolation. Loading never executes file content or prints the credential.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

DEFAULT_ENV_FILE = Path(__file__).resolve().parents[1] / '.env'
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, help='Override the repository-root .env path')
    parser.add_argument('--check-api', action='store_true', help='Make one authenticated, read-only ESR commodity-directory request')
    args = parser.parse_args(argv)
    try:
        key = load_api_key(args.env_file)
    except (ValueError, OSError, UnicodeError):
        print('API key unavailable or invalid. Check the .env setting or process environment.', file=sys.stderr)
        return 2
    if not args.check_api:
        print('API key loaded. No network request made; credential value is hidden.')
        return 0
    request = urllib.request.Request(
        'https://api.fas.usda.gov/api/esr/commodities',
        headers={'X-Api-Key': key, 'Accept': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read(2_000_001)
            if len(payload) > 2_000_000:
                raise ValueError('Response exceeds size limit')
            json.loads(payload)
            print(f'API request succeeded: HTTP {response.status}; JSON received.')
    except urllib.error.HTTPError as exc:
        print(f'API request failed: HTTP {exc.code}.', file=sys.stderr)
        return 1
    except (urllib.error.URLError, OSError, ValueError):
        print('API request failed: network error or invalid JSON response.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
