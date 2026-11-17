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


from usda_data.credentials import load_api_key


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, help='Override the repository-root .env path')
    parser.add_argument('--check-api', action='store_true', help='Make one authenticated, read-only ESR commodity-directory request')
    args = parser.parse_args(argv)
    try:
        key = load_api_key(args.env_file or DEFAULT_ENV_FILE)
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
