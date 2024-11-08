from contextlib import contextmanager
from dataclasses import dataclass, field
from shlex import join, quote
from subprocess import run
from typing import Iterator
from .base import Executor


@dataclass
class Alias:
    cat: str = 'cat'
    docker: str = 'docker'
    sh: str = 'sh'


@dataclass
class Docker[Redirect](Executor[Redirect]):
    executor: Executor[Redirect]
    name: str
    options: list[str] = field(default_factory=list)
    pidfile: str = '/var/run/simp.pid'
    alias: Alias = field(default_factory=Alias)

    def exec(self, command: list[str], *args: str) -> list[str]:
        command, inner = [self.alias.docker, 'exec'], command
        command += args
        command += self.options
        command += [self.name]
        command += inner
        return command

    def wrap(self, command: list[str]) -> list[str]:
        return [self.alias.sh, '-c', f'echo $$ > {quote(self.pidfile)}; exec {join(command)};']

    def getpid(self) -> int:
        command = [self.alias.cat, self.pidfile]
        command = self.exec(command)
        pid = run(command, capture_output=True, text=True, check=True).stdout.strip()
        pid = int(pid)
        return pid

    @contextmanager
    def local(self, command: list[str], *, redirect: Redirect | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        with self.executor.local(command, redirect=redirect, interactive=interactive, tracable=tracable, wait=wait) as pid:
            yield pid

    @contextmanager
    def remote(self, command: list[str], *, redirect: Redirect | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        getpid = lambda: -1

        if tracable:
            command = self.wrap(command)
            getpid = self.getpid

        args = ['-i'] if interactive else []
        command = self.exec(command, *args)

        with self.executor.remote(command, redirect=redirect, interactive=interactive, wait=wait):
            yield getpid()
