"""One bounded HTTP transport with explicit authentication and format failures."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import csv
import io
import json
import logging
import time
import xml.etree.ElementTree as ET
import zipfile
from urllib.parse import parse_qsl
import httpx
from .config import HTTPConfig
from .errors import AuthenticationError, DownloadError, FormatError
from .security import SENSITIVE, safe_url

LOG = logging.getLogger(__name__)

class HTTPClient:
    def __init__(self, config=None, *, transport=None, sleep=time.sleep, now=None):
        self.config = config or HTTPConfig()
        self.sleep = sleep
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.client = httpx.Client(trust_env=self.config.trust_environment, timeout=self.config.timeout_seconds, transport=transport, follow_redirects=False, headers={"User-Agent": "Mozilla/5.0 (compatible; USDA-source-verification/1.0)"})

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.client.close()

    def _delay(self, response, attempt):
        delay = self.config.backoff_seconds * 2 ** attempt
        raw = response.headers.get("retry-after") if response is not None else None
        if raw:
            try:
                delay = float(raw)
            except ValueError:
                try:
                    delay = (parsedate_to_datetime(raw) - self.now()).total_seconds()
                except (TypeError, ValueError, OverflowError):
                    pass
        return min(self.config.max_retry_delay, max(0, delay))

    def get(self, url, *, expected, headers=None):
        """Return verified bytes. Redirects are followed only within the same origin.

        Never log URLs, headers, response bodies, or upstream exception messages.
        All response bodies, including retry bodies, have a strict byte bound.
        """
        target_url = httpx.URL(url)
        if target_url.username or target_url.password or any(SENSITIVE.search(k) for k, _ in parse_qsl(target_url.query.decode())) or any(v and v in str(target_url) for k, v in (headers or {}).items() if SENSITIVE.search(k)):
            raise AuthenticationError("Credentials must be supplied in headers, never in request URLs")
        for attempt in range(self.config.max_attempts):
            response = None
            try:
                target = httpx.URL(url)
                for redirect in range(6):
                    with self.client.stream("GET", target, headers=headers) as response:
                        code = response.status_code
                        if code in {301, 302, 303, 307, 308}:
                            location = response.headers.get("location")
                            if not location or redirect == 5:
                                raise DownloadError("Invalid or excessive redirects")
                            next_url = target.join(location)
                            if (target.scheme, target.host, target.port) != (next_url.scheme, next_url.host, next_url.port):
                                raise DownloadError("Cross-origin redirect requires explicit discovery")
                            target = next_url
                            continue
                        if code in {401, 403}:
                            raise AuthenticationError(f"Source denied access: HTTP {code}")
                        if code == 429 or code in {500, 502, 503, 504}:
                            break
                        if not 200 <= code < 300:
                            raise DownloadError(f"Source returned HTTP {code}")
                        chunks, size = [], 0
                        for chunk in response.iter_bytes():
                            size += len(chunk)
                            if size > self.config.max_response_bytes:
                                raise DownloadError("Response exceeds configured byte limit")
                            chunks.append(chunk)
                        body = b"".join(chunks)
                        verify_format(body, expected, response.headers.get("content-type", ""))
                        return body, {"url": safe_url(str(target)), "status": code, "content_type": response.headers.get("content-type", ""), "last_modified": response.headers.get("last-modified")}
            except (httpx.HTTPError, OSError):
                # Do not chain upstream exceptions: request URLs can contain secrets.
                response = None
            if attempt + 1 == self.config.max_attempts:
                raise DownloadError(f"Request failed after {self.config.max_attempts} attempts") from None
            delay = self._delay(response, attempt)
            LOG.warning("Retry attempt %d/%d in %.3fs", attempt + 2, self.config.max_attempts, delay)
            self.sleep(delay)
        raise DownloadError("Request exhausted")

def verify_format(body, expected, content_type=""):
    prefix = body.lstrip()[:1024].lower()
    if expected != "html" and ("text/html" in content_type.lower() or b"<html" in prefix or b"<!doctype html" in prefix):
        raise FormatError("HTML received instead of requested data format")
    try:
        if expected == "json":
            parsed = json.loads(body)
            if not isinstance(parsed, (dict, list)):
                raise ValueError()
        elif expected == "xml":
            ET.fromstring(body)
        elif expected == "csv":
            reader = csv.reader(io.StringIO(body.decode("utf-8-sig")), strict=True)
            header = next(reader)
            if len(header) < 2:
                raise ValueError()
        elif expected in {"zip", "xlsx"}:
            with zipfile.ZipFile(io.BytesIO(body)) as archive:
                if not archive.namelist() or any(n.startswith("/") or ".." in n.split("/") for n in archive.namelist()):
                    raise ValueError()
        elif expected == "xls":
            if not body.startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
                raise ValueError()
        elif expected == "pdf":
            if not body.startswith(b"%PDF-") or b"%%EOF" not in body[-2048:]:
                raise ValueError()
        elif expected == "html":
            if b"<html" not in prefix and b"<!doctype html" not in prefix:
                raise ValueError()
        else:
            raise FormatError("Unsupported expected response format")
    except (ValueError, UnicodeError, ET.ParseError, csv.Error, StopIteration, zipfile.BadZipFile):
        raise FormatError(f"Invalid {expected} response") from None
