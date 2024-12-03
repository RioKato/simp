from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from typing import Callable, Iterator
from .base import Executor, Launcher

__all__ = [
    'Alias', 'Attacher', 'Debugger'
]


@dataclass
class Alias:
    env: str = 'env'
    frida: str = 'frida'
    frida_server: str = 'frida-server'
    setarch: str = 'setarch'


@dataclass
class Debugger(Launcher[None]):
    command: list[str]
    script: str
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

        command += [self.alias.frida_server]
        return command

    def cli(self) -> list[str]:
        command = [self.alias.frida, '-R', '-l', self.script]
        command += self.options
        command += ['--']
        command += self.command
        return command

    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[None]:
        with executor.remote(self.run(), redirect=redirect, interactive=bool(redirect)):
            with executor.local(self.cli(), interactive=True):
                yield


@dataclass
class Attacher(Launcher[Callable[[], None]]):
    command: list[str]
    script: str
    env: dict[str, str] = field(default_factory=dict)
    aslr: bool = True
    options: list[str] = field(default_factory=list)
    alias: Alias = field(default_factory=Alias)

    def prepare(self) -> list[str]:
        return [self.alias.frida_server]

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
        command = [self.alias.frida, '-R', '-l', self.script, '-p', f'{pid}']
        command += self.options
        command += ['--']
        command += self.command
        return command

    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[Callable[[], None]]:
        with executor.remote(self.prepare(), interactive=False):
            with executor.remote(self.run(), redirect=redirect, interactive=bool(redirect), tracable=True) as pid:
                with ExitStack() as estack:
                    def attach():
                        estack.enter_context(executor.local(self.cli(pid), interactive=True))

                    yield attach
