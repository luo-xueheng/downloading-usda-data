# Shared foundation

Requires Python 3.11 or newer. The declared runtime is tested on Python 3.13.
Install with `python -m pip install -e '.[dev]'` in an isolated environment.

Raw artifact identity is SHA-256 of exact response bytes. Acquisition receipts
are separate, sanitized records; checking the same bytes again retains one blob.
Normalized identity includes artifact hashes, parser version, complete versioned
schema and validated configuration. Inconsistent output for identical identity
fails instead of silently replacing historical results. Snapshot files are
immutable. Only a flushed atomic manifest replacement selects the latest version.
Failed publication preserves the previous pointer; orphan prepared versions are
safe and can be reused on resume. Phase 08/09 adds cross-partition complete-run publication and an operating-system
writer lock: concurrent fetch/sync writers are rejected before state mutation.

CSV uses UTF-8, fixed ordered headers, ISO dates/UTC timestamps and exact Decimal
text. Explicit null is `\N`; literal leading backslashes are escaped by one extra
backslash. Empty string, zero and null are distinct. Codes are strings. Pandas
float inference is never used. Use `Schema.read_csv` for lossless reload. Generic
readers must apply the sidecar schema and documented null/escape rules.

HTTP uses connect/read/write/pool timeouts, finite attempts and capped Retry-After
(seconds or HTTP date). 401/403 fail immediately. Transient 429/500/502/503/504
retry. Authentication values, URLs and raw server exception messages never enter
retry logs. Redirects remain on the same origin to avoid leaking API headers.
Raw source response bytes are preserved; authentication failures are never saved
as valid source artifacts. Only bounded responses enter memory. Source-specific
streaming/partition iteration is added with each adapter.

Initial contracts define provenance and storage rather than asserting unverified
business dimensions. Each adapter must freeze its complete actual business schema
before passing its own phase. Release date/time and retrieval time remain distinct.
No live USDA test is mandatory for Phase 01; synthetic fixtures test only shared
behavior and do not claim source accuracy.
