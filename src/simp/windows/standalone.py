from contextlib import contextmanager
from dataclasses import dataclass
from subprocess import STARTF_USESTDHANDLES, STARTUPINFO, STD_INPUT_HANDLE, STD_OUTPUT_HANDLE, STD_ERROR_HANDLE, Popen
from sys import stderr, stdin, stdout
from typing import Iterator
from .socketbridge import WinSocket
from ..simp import Executor


@dataclass
class Standalone(Executor[WinSocket]):
    @contextmanager
    def local(self, command: list[str], *, redirect: WinSocket | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        if interactive:
            hStdInput = redirect.fileno() if redirect else STD_INPUT_HANDLE
            hStdOutput = redirect.fileno() if redirect else STD_OUTPUT_HANDLE
            hStdError = redirect.fileno() if redirect else STD_ERROR_HANDLE
        else:
            hStdInput = redirect.fileno() if redirect else None
            hStdOutput = redirect.fileno() if redirect else STD_OUTPUT_HANDLE
            hStdError = redirect.fileno() if redirect else STD_ERROR_HANDLE

        startupinfo = STARTUPINFO(
            dwFlags=STARTF_USESTDHANDLES,
            hStdInput=hStdInput,
            hStdOutput=hStdOutput,
            hStdError=hStdError
        )

        with Popen(command, close_fds=False, startupinfo=startupinfo) as popen:
            try:
                yield popen.pid
            finally:
                if not wait and popen.poll() is None:
                    popen.terminate()

    @contextmanager
    def remote(self, command: list[str], *, redirect: WinSocket | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        with self.local(command, redirect=redirect, interactive=interactive, tracable=tracable, wait=wait) as pid:
            yield pid
