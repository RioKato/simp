from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator
from simp import Client, Development, Launcher, SocketBridge, Standalone, Tmux
from socket import socket
from ..socketupgrader import SocketMonitor, SocketUpgrader


@dataclass
class EasyDevelopment[Helper]:
    development: Development[Helper, socket, socket]

    def __init__(self, launcher: Launcher[Helper], method: Client[socket] | None, tmux: bool = False):
        executor = Standalone()

        if tmux:
            executor = Tmux(executor)

        if method:
            method_ = method
        else:
            method_ = SocketBridge()

        self.development = Development(executor=executor, launcher=launcher, method=method_)

    @contextmanager
    def __call__(self) -> Iterator[tuple[SocketMonitor, Helper]]:
        with self.development() as (connection, helper):
            with SocketUpgrader()(connection) as upgraded:
                yield (upgraded, helper)
