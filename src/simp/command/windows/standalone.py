from contextlib import contextmanager
from ctypes import WinError, windll
from ctypes.wintypes import DWORD, HANDLE
from dataclasses import dataclass
from os import set_handle_inheritable
from subprocess import CREATE_NEW_CONSOLE, STARTF_USESTDHANDLES, STARTUPINFO, STD_INPUT_HANDLE, STD_OUTPUT_HANDLE, STD_ERROR_HANDLE, Popen
from typing import Iterator
from .socketbridge import WinSocket
from ..base import Executor


INVALID_HANDLE_VALUE = -1
_GetStdHandle = windll.kernel32.GetStdHandle
_GetStdHandle.argtypes = [DWORD]
_GetStdHandle.restype = HANDLE


def GetStdHandle(nStdHandle: int) -> int:
    handle = _GetStdHandle(nStdHandle)

    if handle == INVALID_HANDLE_VALUE:
        raise WinError()

    return handle


@dataclass
class Standalone(Executor[WinSocket]):
    @contextmanager
    def local(self, command: list[str], *, redirect: WinSocket | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        creationflags = 0

        if interactive:
            if redirect:
                hStdInput = redirect.fileno()
            else:
                hStdInput = GetStdHandle(STD_INPUT_HANDLE)
                creationflags |= CREATE_NEW_CONSOLE
        else:
            hStdInput = INVALID_HANDLE_VALUE

        hStdOutput = redirect.fileno() if redirect else GetStdHandle(STD_OUTPUT_HANDLE)
        hStdError = redirect.fileno() if redirect else GetStdHandle(STD_ERROR_HANDLE)
        handle_list = [hStdInput, hStdOutput, hStdError]
        handle_list = list(set(h for h in handle_list if h != INVALID_HANDLE_VALUE))

        for handle in handle_list:
            set_handle_inheritable(handle, True)

        startupinfo = STARTUPINFO(
            dwFlags=STARTF_USESTDHANDLES,
            hStdInput=hStdInput,
            hStdOutput=hStdOutput,
            hStdError=hStdError,
            lpAttributeList=dict(handle_list=handle_list)
        )

        with Popen(command, startupinfo=startupinfo, creationflags=creationflags) as popen:
            try:
                yield popen.pid
            finally:
                if not wait and popen.poll() is None:
                    popen.terminate()

    @contextmanager
    def remote(self, command: list[str], *, redirect: WinSocket | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        with self.local(command, redirect=redirect, interactive=interactive, tracable=tracable, wait=wait) as pid:
            yield pid
