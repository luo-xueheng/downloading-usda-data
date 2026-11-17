"""Reject corrupted source evidence using the independent standard-library verifier."""
import importlib.util
from pathlib import Path


def test_phase00_rejection_paths(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "tools/check_phase00_rejections.py"
    spec = importlib.util.spec_from_file_location("phase00_rejections", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # The legacy harness also disables urllib; restore it after this test.
    monkeypatch.setattr(module.urllib.request, "urlopen", module.urllib.request.urlopen)
    module.run(tmp_path)
