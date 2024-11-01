from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator
from simp import Client, Development, Launcher, SocketBridge, Standalone, WSAStartup, WinSocket
from socket import socket
from ..socketupgrader import SocketMonitor, SocketUpgrader


@dataclass
class EasyDevelopment[Helper]:
    development: Development[Helper, socket, WinSocket]

    def __init__(self, launcher: Launcher[Helper], method: Client[socket] | None, laddr: str = '0.0.0.0', caddr: str = '127.0.0.1'):
        executor = Standalone()

        if method:
            method_ = method
        else:
            method_ = SocketBridge(laddr=laddr, caddr=caddr)

        self.development = Development(executor=executor, launcher=launcher, method=method_)

    @contextmanager
    def __call__(self) -> Iterator[tuple[SocketMonitor, Helper]]:
        with WSAStartup():
            with self.development() as (connection, helper):
                with SocketUpgrader()(connection) as upgraded:
                    yield (upgraded, helper)
