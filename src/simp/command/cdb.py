from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from typing import Callable, Iterator
from .base import Executor, Launcher


__all__ = [
    'Alias', 'Attacher', 'Debugger'
]


@dataclass
class Alias:
    cdb: str = 'cdb.exe'


@dataclass
class Debugger(Launcher[None]):
    command: list[str]
    port: int = 1234
    alias: Alias = field(default_factory=Alias)

    def debug(self) -> list[str]:
        command = [self.alias.cdb, '-server', f'tcp:port={self.port}']
        command += self.command
        return command

    def cli(self) -> list[str]:
        return [self.alias.cdb, '-remote', f'tcp:port={self.port}']

    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[None]:
        with executor.remote(self.debug(), redirect=redirect, interactive=bool(redirect)):
            with executor.local(self.cli(), interactive=True):
                yield


@dataclass
class Attacher(Launcher[Callable[[], None]]):
    command: list[str]
    port: int = 1234
    alias: Alias = field(default_factory=Alias)

    def run(self) -> list[str]:
        return self.command

    def attach(self, pid: int) -> list[str]:
        return [self.alias.cdb, '-server', f'tcp:port={self.port}', '-p', f'{pid}']

    def cli(self) -> list[str]:
        return [self.alias.cdb, '-remote', f'tcp:port={self.port}']

    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[Callable[[], None]]:
        with executor.remote(self.run(), redirect=redirect, interactive=bool(redirect), tracable=True) as pid:
            with ExitStack() as estack:
                def attach():
                    estack.enter_context(executor.remote(self.attach(pid)))
                    estack.enter_context(executor.local(self.cli(), interactive=True))

                yield attach
