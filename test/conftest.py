"""Offline regression tests use temporary outputs; live/archive checks are opt-in."""
from pathlib import Path
import os
import socket
import pytest


def pytest_collection_modifyitems(config, items):
    for item in items:
        if item.get_closest_marker("historical") and not os.environ.get("USDA_ARCHIVE_ROOT"):
            item.add_marker(pytest.mark.skip(reason="Set USDA_ARCHIVE_ROOT to the archived original checkout"))


@pytest.fixture(scope="module", autouse=True)
def isolated_module_output(request, tmp_path_factory):
    """Keep module-level fixture results together without writing into the repository."""
    module = request.module
    if hasattr(module, "OUT"):
        # Historical tests intentionally read their immutable external evidence.
        if "historical" in Path(module.__file__).parts:
            yield
            return
        previous = module.OUT
        module.OUT = tmp_path_factory.mktemp(module.__name__.replace(".", "-"))
        (module.OUT / "live").mkdir()
        (module.OUT / "resume").mkdir()
        try:
            yield
        finally:
            module.OUT = previous
    else:
        yield


@pytest.fixture(autouse=True)
def forbid_offline_network(request, monkeypatch):
    if request.node.get_closest_marker("live"):
        return
    def denied(*args, **kwargs):
        raise AssertionError("Offline test attempted a real network connection")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
