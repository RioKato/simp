from dataclasses import dataclass
from socket import socket, socketpair
from ..base import Bridge


@dataclass
class SocketBridge(Bridge[socket, socket]):
    def __call__(self) -> tuple[socket, socket]:
        return socketpair()
