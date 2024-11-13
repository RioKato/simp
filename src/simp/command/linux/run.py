from contextlib import contextmanager
from socket import socket
from typing import Iterator
from .socketbridge import SocketBridge
from .standalone import Standalone
from ..base import Executor, Launcher, run as brun


@contextmanager
def run[Helper](
        launcher: Launcher[Helper],
        executor: Executor[socket] = Standalone(), *,
        redirect: bool = False) -> Iterator[tuple[Helper, socket | None]]:

    bridge = SocketBridge() if redirect else None

    with brun(launcher, executor, bridge) as (helper, connection):
        yield (helper, connection)
