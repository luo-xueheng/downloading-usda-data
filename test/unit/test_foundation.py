from datetime import date, datetime, timezone
from decimal import Decimal
import importlib.metadata
import json
import logging
from pathlib import Path
import subprocess
import sys
import traceback
import httpx
import pandas as pd
import pytest
from usda_data.config import HTTPConfig
from usda_data.errors import AuthenticationError, DownloadError, FormatError, ValidationError
from usda_data.http import HTTPClient
from usda_data.schema import Schema
from usda_data.storage import Store, atomic_write
from usda_data.state import PartitionState, RunManifest

ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture
def sample():
    schema = Schema.load(ROOT / "test/fixtures/schemas/roundtrip.v1.json")
    rows = json.loads((ROOT / "test/fixtures/roundtrip.json").read_text())["records"]
    for row in rows:
        row["date"] = date.fromisoformat(row["date"])
        row["amount"] = Decimal(row["amount"])
    return schema, schema.frame(rows)

@pytest.mark.acceptance("P01-A1")
def test_installed_import_help():
    assert importlib.metadata.version("usda-data") == "0.1.0"
    for args in [["--help"], ["--version"], ["list-datasets"]]:
        result = subprocess.run([sys.executable, "-m", "usda_data", *args], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert result.stdout
    assert len(subprocess.check_output([sys.executable, "-m", "usda_data", "list-datasets"], text=True).splitlines()) == 7

@pytest.mark.acceptance("P01-A2")
def test_csv_exact_roundtrip(sample, tmp_path):
    schema, frame = sample
    path = tmp_path / "output.csv"
    schema.write_csv(frame, path)
    actual = schema.read_csv(path)
    pd.testing.assert_frame_equal(actual, frame)
    assert actual.iloc[0]["code"] == "001"
    assert actual.iloc[0]["amount"].as_tuple() == Decimal("-12.3400").as_tuple()
    assert actual.iloc[0]["missing"] is None
    assert actual.iloc[1]["text"] == "\\N"
    assert actual.iloc[2]["text"] == ""

@pytest.mark.acceptance("P01-A3")
def test_content_and_snapshot_identity(sample, tmp_path):
    schema, frame = sample
    store = Store(tmp_path)
    a = store.raw(b"official bytes", metadata={})
    b = store.raw(b"official bytes", metadata={})
    c = store.raw(b"official byteS", metadata={})
    assert a["source_artifact_id"] == b["source_artifact_id"] != c["source_artifact_id"]
    first = store.publish("test", "2026", frame, schema, [a["source_artifact_id"]], parser_version="1", configuration={})
    same = store.publish("test", "2026", frame, schema, [a["source_artifact_id"]], parser_version="1", configuration={})
    changed_parser = store.publish("test", "2026", frame, schema, [a["source_artifact_id"]], parser_version="2", configuration={})
    changed_schema = store.publish("test", "2026", frame, Schema(schema.name,"2",schema.fields), [a["source_artifact_id"]], parser_version="1", configuration={})
    changed_config = store.publish("test", "2026", frame, schema, [a["source_artifact_id"]], parser_version="1", configuration={"x":1})
    assert first == same
    assert len({m["snapshot_id"] for m in [first, changed_parser, changed_schema, changed_config]}) == 4
    assert (tmp_path / first["csv_path"]).exists()

@pytest.mark.acceptance("P01-A4")
def test_failed_publication_preserves_selected_version(sample, tmp_path):
    schema, frame = sample
    store = Store(tmp_path)
    a = store.raw(b"A", metadata={})
    previous = store.publish("test", "2026", frame, schema, [a["source_artifact_id"]], parser_version="1", configuration={})
    pointer = tmp_path / "manifests/test/2026.latest.json"
    before = pointer.read_bytes()
    file_before = (tmp_path / previous["csv_path"]).read_bytes()
    def failure():
        raise OSError("Injected publication interruption")
    with pytest.raises(OSError):
        store.publish("test", "2026", frame, schema, [a["source_artifact_id"]], parser_version="2", configuration={}, before_publish=failure)
    assert pointer.read_bytes() == before
    assert store.latest("test", "2026") == previous
    assert (tmp_path / previous["csv_path"]).read_bytes() == file_before
    assert not list(tmp_path.rglob(".pending-*"))
    with pytest.raises(OSError):
        atomic_write(pointer, b"incomplete", before_replace=failure)
    assert pointer.read_bytes() == before

@pytest.mark.acceptance("P01-A5")
@pytest.mark.parametrize("code",[429,500,502,503,504])
def test_bounded_retries(code):
    calls, delays = [], []
    def handler(request):
        calls.append(request)
        return httpx.Response(code, headers={"Retry-After":"999999"})
    with HTTPClient(HTTPConfig(max_attempts=3,max_retry_delay=2), transport=httpx.MockTransport(handler), sleep=delays.append) as client:
        with pytest.raises(DownloadError, match="3 attempts"):
            client.get("https://example.test/data", expected="json")
    assert len(calls) == 3 and delays == [2,2]

@pytest.mark.acceptance("P01-A5")
def test_retry_success_http_date_and_timeout():
    replies = iter([httpx.Response(429,headers={"Retry-After":"Thu, 15 Jan 2026 17:00:02 GMT"}),httpx.Response(200,json={"ok":True})])
    delays = []
    with HTTPClient(transport=httpx.MockTransport(lambda r:next(replies)),sleep=delays.append,now=lambda:datetime(2026,1,15,17,tzinfo=timezone.utc)) as client:
        assert client.get("https://example.test/data",expected="json")[0] == b'{"ok":true}'
    assert delays == [2]
    calls=[]
    def timeout(request):
        calls.append(request)
        raise httpx.ReadTimeout("injected")
    with HTTPClient(transport=httpx.MockTransport(timeout),sleep=lambda _:None) as client:
        with pytest.raises(DownloadError):
            client.get("https://example.test/data",expected="csv")
    assert len(calls)==3

@pytest.mark.acceptance("P01-A5")
@pytest.mark.parametrize("code",[401,403])
def test_auth_fails_without_retry(code):
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(code)
    with HTTPClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AuthenticationError, match=str(code)):
            client.get("https://example.test/data",expected="json")
    assert len(calls)==1

@pytest.mark.acceptance("P01-A5")
@pytest.mark.parametrize("expected",["csv","json"])
def test_reject_html(expected):
    with HTTPClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,content=b"<!DOCTYPE html><html>login</html>"))) as client:
        with pytest.raises(FormatError):
            client.get("https://example.test/data",expected=expected)

@pytest.mark.acceptance("P01-A6")
def test_no_secret_in_logs_tracebacks_or_manifests(tmp_path,caplog):
    secret="SYNTHETIC_SENTINEL_DO_NOT_PERSIST"
    caplog.set_level(logging.DEBUG)
    def handler(request):
        assert request.headers["X-Api-Key"]==secret
        raise httpx.ConnectError("server echoed "+secret)
    with HTTPClient(transport=httpx.MockTransport(handler),sleep=lambda _:None) as client:
        try:
            client.get("https://example.test/data",expected="json",headers={"X-Api-Key":secret})
        except DownloadError:
            diagnostic=traceback.format_exc()
    assert secret not in diagnostic+caplog.text
    store=Store(tmp_path,secrets=[secret])
    store.raw(b"nonsecret official data",metadata={"headers":{"X-Api-Key":secret},"url":"https://example.test/data?key="+secret,"error":secret})
    RunManifest("run","test","hash",partitions=[PartitionState("p",reason=secret)]).save(store)
    assert all(secret.encode() not in p.read_bytes() for p in tmp_path.rglob("*.json"))

@pytest.mark.acceptance("P01-A7")
def test_strict_layout_dimensions_and_keys(sample):
    schema, frame=sample
    missing=frame.copy();missing.loc[0,"code"]=None
    duplicate=pd.concat([frame,frame.iloc[[0]]],ignore_index=True)
    extra=frame.assign(unexpected="x")
    for bad in [missing,duplicate,extra,frame.drop(columns="amount")]:
        with pytest.raises(ValidationError):
            schema.validate(bad)
    with pytest.raises(ValidationError):
        schema.frame([{"code":"001"}])

@pytest.mark.acceptance("P01-A5")
def test_byte_bound_and_redirect_protection():
    for handler in [lambda r:httpx.Response(200,content=b"a"*100),lambda r:httpx.Response(302,headers={"Location":"https://elsewhere.test/key"})]:
        with HTTPClient(HTTPConfig(max_response_bytes=10),transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(DownloadError):
                client.get("https://example.test/data",expected="csv")

@pytest.mark.acceptance("P01-A3")
def test_corrupted_or_nondeterministic_snapshot_rejected(sample,tmp_path):
    schema,frame=sample;store=Store(tmp_path)
    artifact=store.raw(b"A",metadata={})["source_artifact_id"]
    first=store.publish("test","p",frame,schema,[artifact],parser_version="1",configuration={})
    changed=frame.copy();changed.loc[0,"amount"]=Decimal("1")
    with pytest.raises(ValidationError,match="Nondeterministic"):
        store.publish("test","p",changed,schema,[artifact],parser_version="1",configuration={})
    (tmp_path/first["csv_path"]).write_bytes(b"corrupt")
    with pytest.raises(ValidationError):
        store.latest("test","p")

@pytest.mark.acceptance("P01-A6")
def test_credential_urls_are_rejected_without_logging(caplog):
    secret = "SYNTHETIC_URL_SECRET"
    caplog.set_level(logging.DEBUG)
    with HTTPClient(transport=httpx.MockTransport(lambda r: pytest.fail("credential URL sent"))) as client:
        for url in ["https://example.test/data?api_key=" + secret, "https://user:" + secret + "@example.test/data"]:
            with pytest.raises(AuthenticationError) as captured:
                client.get(url, expected="json")
            assert secret not in str(captured.value) + caplog.text
