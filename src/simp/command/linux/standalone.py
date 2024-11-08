from contextlib import contextmanager
from ctypes import CDLL, c_int, c_ulong
from dataclasses import dataclass
from socket import socket
from subprocess import DEVNULL, Popen, TimeoutExpired
from typing import IO, Iterator, cast
from ..base import Executor


class Glibc:
    PR_SET_PTRACER = 0x59616d61
    PR_SET_PTRACER_ANY = -1

    prctl = CDLL(None).prctl
    prctl.restype = c_int
    prctl.argtypes = [c_int, c_ulong, c_ulong, c_ulong, c_ulong]


@dataclass
class Standalone(Executor[socket]):
    @contextmanager
    def local(self, command: list[str], *, redirect: socket | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        def pr_set_ptracer_any():
            Glibc.prctl(Glibc.PR_SET_PTRACER, Glibc.PR_SET_PTRACER_ANY, 0, 0, 0)

        if interactive:
            stdin = stdout = stderr = cast(IO, redirect) if redirect else None
        else:
            stdin = DEVNULL
            stdout = stderr = cast(IO, redirect) if redirect else None

        preexec_fn = pr_set_ptracer_any if tracable else None

        with Popen(command, stdin=stdin, stdout=stdout, stderr=stderr, process_group=0, preexec_fn=preexec_fn) as popen:
            try:
                yield popen.pid
            finally:
                if not wait and popen.poll() is None:
                    popen.terminate()

                    try:
                        popen.wait(1)
                    except TimeoutExpired:
                        popen.kill()

    @contextmanager
    def remote(self, command: list[str], *, redirect: socket | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        with self.local(command, redirect=redirect, interactive=interactive, tracable=tracable, wait=wait) as pid:
            yield pid
