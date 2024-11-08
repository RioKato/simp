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
    gdb: str = 'gdb'
    gdbserver: str = 'gdbserver'
    setarch: str = 'setarch'


@dataclass
class Debugger(Launcher[None]):
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)
    aslr: bool = True
    host: str = ''
    port: int = 1234
    file: str = ''
    sysroot: str = ''
    startup: str = 'target remote {host}:{port}'
    script: str = ''
    options: list[str] = field(default_factory=list)
    alias: Alias = field(default_factory=Alias)

    def debug(self) -> list[str]:
        command = [self.alias.gdbserver]

        if self.aslr:
            command += ['--no-disable-randomization']
        else:
            command += ['--disable-randomization']

        if self.env:
            command += ['--wrapper', self.alias.env]

            for k, v in self.env.items():
                command += [f'{k}={v}']

            command += ['--']

        command += self.options
        command += [f'{self.host}:{self.port}']
        command += self.command
        return command

    def cli(self) -> list[str]:
        command = [self.alias.gdb]

        if self.sysroot:
            command += ['-ex', f'set sysroot {self.sysroot}']

        startup = self.startup.format(host=self.host, port=self.port)
        command += ['-ex', startup]

        if self.script:
            command += ['-x', self.script]

        if self.file:
            command += [self.file]

        return command

    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[None]:
        with executor.remote(self.debug(), redirect=redirect, interactive=bool(redirect)):
            with executor.local(self.cli(), interactive=True):
                yield


@dataclass
class Attacher(Launcher[Callable[[], None]]):
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)
    aslr: bool = True
    host: str = ''
    port: int = 1234
    file: str = ''
    sysroot: str = ''
    startup: str = 'target remote {host}:{port}'
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

        command += self.command
        return command

    def attach(self, pid: int) -> list[str]:
        return [self.alias.gdbserver, '--attach', f'{self.host}:{self.port}', f'{pid}']

    def cli(self) -> list[str]:
        command = [self.alias.gdb]

        if self.sysroot:
            command += ['-ex', f'set sysroot {self.sysroot}']

        startup = self.startup.format(host=self.host, port=self.port)
        command += ['-ex', startup]

        if self.script:
            command += ['-x', self.script]

        if self.file:
            command += [self.file]

        return command

    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[Callable[[], None]]:
        with executor.remote(self.run(), redirect=redirect, interactive=bool(redirect), tracable=True) as pid:
            with ExitStack() as estack:
                def attach():
                    estack.enter_context(executor.remote(self.attach(pid)))
                    estack.enter_context(executor.local(self.cli(), interactive=True))

                yield attach
