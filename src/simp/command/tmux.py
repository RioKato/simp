from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator
from .base import Executor


@dataclass
class Alias:
    tmux: str = 'tmux'


@dataclass
class Tmux[Redirect](Executor[Redirect]):
    executor: Executor[Redirect]
    options: list[str] = field(default_factory=list)
    alias: Alias = field(default_factory=Alias)

    def split(self, command: list[str]) -> list[str]:
        command, innner = [self.alias.tmux, 'split'], command
        command += self.options
        command += innner
        return command

    @contextmanager
    def local(self, command: list[str], *, redirect: Redirect | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        if not redirect and interactive:
            command = self.split(command)
            interactive = False
            wait = True

        with self.executor.local(command, redirect=redirect, interactive=interactive, tracable=tracable, wait=wait) as pid:
            yield pid

    @contextmanager
    def remote(self, command: list[str], *, redirect: Redirect | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        if not redirect and interactive:
            command = self.split(command)
            interactive = False
            wait = True

        with self.executor.remote(command, redirect=redirect, interactive=interactive, tracable=tracable, wait=wait) as pid:
            yield pid
