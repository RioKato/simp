from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from msvcrt import get_osfhandle
from os import O_RDWR, close, devnull, open as osopen
from subprocess import STARTF_USESTDHANDLES, STARTUPINFO, STD_INPUT_HANDLE, STD_OUTPUT_HANDLE, STD_ERROR_HANDLE, Popen
from typing import Iterator
from .socketbridge import WinSocket
from ..base import Executor


@contextmanager
def closefd(fd: int) -> Iterator[None]:
    try:
        yield
    finally:
        close(fd)


@dataclass
class Standalone(Executor[WinSocket]):
    @contextmanager
    def local(self, command: list[str], *, redirect: WinSocket | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        with ExitStack() as estack:
            if interactive:
                hStdInput = redirect.fileno() if redirect else STD_INPUT_HANDLE
                hStdOutput = redirect.fileno() if redirect else STD_OUTPUT_HANDLE
                hStdError = redirect.fileno() if redirect else STD_ERROR_HANDLE
            else:
                if redirect:
                    hStdInput = redirect.fileno()
                else:
                    fd = osopen(devnull, O_RDWR)
                    estack.enter_context(closefd(fd))
                    hStdInput = get_osfhandle(fd)

                hStdOutput = redirect.fileno() if redirect else STD_OUTPUT_HANDLE
                hStdError = redirect.fileno() if redirect else STD_ERROR_HANDLE

            startupinfo = STARTUPINFO(
                dwFlags=STARTF_USESTDHANDLES,
                hStdInput=hStdInput,
                hStdOutput=hStdOutput,
                hStdError=hStdError
            )

            with Popen(command, close_fds=False, startupinfo=startupinfo) as popen:
                estack.pop_all().close()

                try:
                    yield popen.pid
                finally:
                    if not wait and popen.poll() is None:
                        popen.terminate()

    @contextmanager
    def remote(self, command: list[str], *, redirect: WinSocket | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        with self.local(command, redirect=redirect, interactive=interactive, tracable=tracable, wait=wait) as pid:
            yield pid
