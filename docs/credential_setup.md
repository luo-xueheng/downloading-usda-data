# FAS API credentials

> Repository cleanup (2026-11-17): historical `artifacts/` and full `data/` paths below refer to the external archive. See [migration and archive guide](repository_cleanup.md). These saved results are not current test results.


## Automatic local loading

Open `.env` in the repository root and paste your own FAS/api.data.gov key after the equals sign:

```dotenv
USDA_FAS_API_KEY=
```

The file has been created with an empty value. Do not leave the value empty when using the API. `.env` and `.env.*` are ignored by Git; `.env.example` contains only an empty template and may be committed. Keep the real key out of chat, source code and logs.

From the repository root, check that the key can be loaded:

```bash
.venv/bin/python scripts/fas_credentials.py
```

This reads the project-root `.env` automatically, prints only whether loading succeeded, and makes no network request. It also works when launched from another directory using the script's absolute path. The file is loaded into that Python process; it does not change an already-open terminal's environment.

Optionally check real API access with a single read-only request:

```bash
.venv/bin/python scripts/fas_credentials.py --check-api
```

Success reports HTTP 200 and confirms a JSON response from the ESR commodity directory. Failure prints only the HTTP status or a generic network/format error, never the key or response headers. This convenience check is not Phase 04/05 acceptance and does not save source fixtures.

To use a different file:

```bash
.venv/bin/python scripts/fas_credentials.py --env-file /absolute/path/to/credentials.env
```

A nonempty existing `USDA_FAS_API_KEY` environment variable takes precedence over the file. If an old terminal value is overriding a new `.env` value, run `unset USDA_FAS_API_KEY` in that terminal before launching Python again.

The loader accepts blank lines, full-line comments and a single `USDA_FAS_API_KEY=value` assignment, optionally with matching quotes or a leading `export `. Keep comments on separate lines. It does not execute shell commands, expand variables or support multiline keys.

## Using the helper from Python

Run from the repository root:

```python
from scripts.fas_credentials import load_api_key

key = load_api_key()
headers = {"X-Api-Key": key, "Accept": "application/json"}
# Pass headers to your HTTP request. Do not print key or headers.
```

This is an explicit helper call: arbitrary scripts do not automatically read `.env`. Future authenticated ESR/PSD adapters should call this helper or preserve the same environment-first loading behavior. Existing Phase 00 public-source tools remain unauthenticated and do not load the key.

## Registration and phase boundaries

The official FAS portal is `https://apps.fas.usda.gov/opendataweb/home`. Its signup flow supplies an api.data.gov key; the saved official Swagger defines `X-Api-Key` in the request header. If registration is needed, use the user's real Nexus email only after it is supplied and registration is authorized. The email owner completes verification.

The original Phase 00 run on 2026-11-12 had no API credential. Its saved acceptance results remain historical evidence for that source-tree hash. The user-authorized .env convenience change on 2026-11-14 does not advance Phases 01-10 or establish authenticated source acceptance. Rerunning Phase 00 after this change produces a different source-tree hash and requires both verification modes for a new combined acceptance result.

Official authentication evidence: `artifacts/acceptance/phase-00/discovery/swagger.json` and `portal-main.js`. Full response schemas, dictionary coverage and ESR/PSD data validation remain tasks for Phases 04/05.

## Phase 04 verified API access

Authenticated ESR dictionary, commodity/year and destination-specific requests succeeded on 2026-11-15. The package loads USDA_FAS_API_KEY from the environment or working-directory .env at call time. On this workstation proxy connections failed, but direct TLS succeeded; config/datasets.toml explicitly sets fas_http.trust_environment=false. Use the package CLI for the configured transport. The older standalone credential helper retains its original urllib transport and can still fail through the local proxy; such failure alone does not invalidate the key.
