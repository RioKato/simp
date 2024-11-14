from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from typing import Callable, Iterator
from .base import Executor, Launcher

__all__ = [
    'Alias', 'Debugger', 'Attacher'
]


@dataclass
class Alias:
    env: str = 'env'
    ltrace: str = 'ltrace'
    setarch: str = 'setarch'


@dataclass
class Debugger(Launcher[None]):
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)
    aslr: bool = True
    options: list[str] = field(default_factory=list)
    alias: Alias = field(default_factory=Alias)

    def debug(self) -> list[str]:
        command = []

        if not self.aslr:
            command += [self.alias.setarch, '-R']

        if self.env:
            command += [self.alias.env]

            for k, v in self.env.items():
                command += [f'{k}={v}']

        command += [self.alias.ltrace]
        command += self.options
        command += self.command
        return command

    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[None]:
        with executor.remote(self.debug(), redirect=redirect, interactive=bool(redirect)):
            yield


@dataclass
class Attacher(Launcher[Callable[[], None]]):
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)
    aslr: bool = True
    options: list[str] = field(default_factory=list)
    alias: Alias = field(default_factory=Alias)

    def run(self) -> list[str]:
        command = []

        if not self.aslr:
            command += [self.alias.setarch, '-R']

        if self.env:
            command += [self.alias.env]

            for k, v in self.env.items():
                command += [f'{k}={v}']

        command += self.command
        return command

    def cli(self, pid: int) -> list[str]:
        command = [self.alias.ltrace]
        command += self.options
        command += ['-p', f'{pid}']
        return command

    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[Callable[[], None]]:
        with executor.remote(self.run(), redirect=redirect, interactive=bool(redirect), tracable=True) as pid:
            with ExitStack() as estack:
                def attach():
                    estack.enter_context(executor.remote(self.cli(pid), interactive=True))

                yield attach
