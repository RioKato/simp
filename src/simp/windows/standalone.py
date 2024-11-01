from contextlib import contextmanager
from dataclasses import dataclass
from subprocess import STARTF_USESTDHANDLES, STARTUPINFO, Popen
from sys import stderr, stdin, stdout
from typing import Iterator
from .socketbridge import WinSocket
from ..simp import Executor


@dataclass
class Standalone(Executor[WinSocket]):
    @contextmanager
    def local(self, command: list[str], *, redirect: WinSocket | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        if interactive:
            hStdInput = redirect.fileno() if redirect else stdin.fileno()
            hStdOutput = redirect.fileno() if redirect else stdout.fileno()
            hStdError = redirect.fileno() if redirect else stderr.fileno()
        else:
            hStdInput = redirect.fileno() if redirect else None
            hStdOutput = redirect.fileno() if redirect else stdout.fileno()
            hStdError = redirect.fileno() if redirect else stderr.fileno()

        startupinfo = STARTUPINFO(
            dwFlags=STARTF_USESTDHANDLES,
            hStdInput=hStdInput,
            hStdOutput=hStdOutput,
            hStdError=hStdError
        )

        with Popen(command, startupinfo=startupinfo) as popen:
            try:
                yield popen.pid
            finally:
                if not wait and popen.poll() is None:
                    popen.terminate()

    @contextmanager
    def remote(self, command: list[str], *, redirect: WinSocket | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        with self.local(command, redirect=redirect, interactive=interactive, tracable=tracable, wait=wait) as pid:
            yield pid
