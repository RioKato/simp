from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator
from .base import Executor, Launcher

__all__ = [
    'Alias', 'Runner'
]


@dataclass
class Alias:
    env: str = 'env'
    setarch: str = 'setarch'


@dataclass
class Runner(Launcher[None]):
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)
    aslr: bool = True
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

    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[None]:
        with executor.remote(self.run(), redirect=redirect, interactive=bool(redirect)):
            yield
