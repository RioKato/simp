from contextlib import contextmanager
from socket import socket
from typing import Iterator
from .socketbridge import SocketBridge
from ..base import Executor, Launcher, execcmd as bexeccmd


@contextmanager
def execcmd[Helper](launcher: Launcher[Helper], executor: Executor[socket], *, redirect: bool = False) -> Iterator[tuple[socket | None, Helper]]:
    bridge = SocketBridge() if redirect else None

    with bexeccmd(launcher, executor, bridge) as (connection, helper):
        yield (connection, helper)
