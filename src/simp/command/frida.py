from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator
from .base import Executor, Launcher


@dataclass
class Alias:
    env: str = 'env'
    frida: str = 'frida'
    frida_server: str = 'frida-server'
    setarch: str = 'setarch'


@dataclass
class Tracer(Launcher[None]):
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)
    aslr: bool = True
    script: str = ''
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
        command += self.command
        return command

    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[None]:
        with executor.remote(self.run(), redirect=redirect, interactive=bool(redirect)):
            with executor.local(self.cli(), interactive=True):
                yield
