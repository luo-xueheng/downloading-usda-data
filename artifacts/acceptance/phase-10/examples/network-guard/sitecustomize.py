import socket
def denied(*a, **k):
    raise AssertionError("Offline example attempted network")
socket.socket.connect=denied
socket.socket.connect_ex=denied
socket.create_connection=denied
