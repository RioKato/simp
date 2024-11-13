from contextlib import contextmanager, nullcontext
from socket import socket
from typing import Iterator
from .socketbridge import SocketBridge, WSAStartup, WinSocket
from .standalone import Standalone
from ..base import Executor, Launcher, run as brun


@contextmanager
def run[Helper](
        launcher: Launcher[Helper],
        executor: Executor[WinSocket] = Standalone(), *,
        redirect: bool = False) -> Iterator[tuple[Helper, socket | None]]:

    bridge = SocketBridge() if redirect else None

    with WSAStartup() if bridge else nullcontext():
        with brun(launcher, executor, bridge) as (helper, connection):
            yield (helper, connection)
