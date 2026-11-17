"""Offline tests are forbidden from opening real network sockets."""
import socket
import pytest

@pytest.fixture(autouse=True)
def forbid_offline_network(request, monkeypatch):
    if request.node.get_closest_marker("live"):
        return
    def denied(*args, **kwargs):
        raise AssertionError("Offline test attempted a real network connection")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
