from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from typing import Callable, Iterator
from .base import Executor, Launcher

__all__ = [
    'Alias', 'Attacher', 'Debugger'
]


@dataclass
class Alias:
    dbgsrv: str = 'linux_server64'
    env: str = 'env'
    ida: str = 'ida64'
    setarch: str = 'setarch'


@dataclass
class Debugger(Launcher[None]):
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)
    aslr: bool = True
    host: str = 'localhost'
    port: int = 1234
    password: str = ''
    debname: str = 'linux'
    options: list[str] = field(default_factory=list)
    alias: Alias = field(default_factory=Alias)

    def prepare(self) -> list[str]:
        command = []

        if not self.aslr:
            command += [self.alias.setarch, '-R']

        if self.env:
            command += [self.alias.env]

            for k, v in self.env.items():
                command += [f'{k}={v}']

        command += [self.alias.dbgsrv]

        if self.host:
            command += ['-i', self.host]

        command += ['-p', f'{self.port}']

        if self.password:
            command += ['-P', self.password]

        command += self.options
        return command

    def debug(self) -> list[str]:
        command = [self.alias.ida, f'-r{self.debname}:{self.password}@{self.host}:{self.port}']
        command += self.command
        return command

    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[None]:
        with executor.remote(self.prepare(), redirect=redirect, interactive=bool(redirect)):
            with executor.local(self.debug()):
                yield


@dataclass
class Attacher(Launcher[Callable[[], None]]):
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)
    aslr: bool = True
    host: str = 'localhost'
    port: int = 1234
    password: str = ''
    debname: str = 'linux'
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

    def prepare(self) -> list[str]:
        command = [self.alias.dbgsrv]

        if self.host:
            command += ['-i', self.host]

        command += ['-p', f'{self.port}']

        if self.password:
            command += ['-P', self.password]

        command += self.options
        return command

    def attach(self, pid: int) -> list[str]:
        return [self.alias.ida, f'-r{self.debname}:{self.password}@{self.host}:{self.port}+{pid}']

    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[Callable[[], None]]:
        with executor.remote(self.prepare()):
            with executor.remote(self.run(), redirect=redirect, interactive=bool(redirect), tracable=True) as pid:
                with ExitStack() as estack:
                    def attach():
                        estack.enter_context(executor.local(self.attach(pid)))

                    yield attach
