from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator
from .base import Executor, Launcher

__all__ = [
    'Alias', 'Debugger', 'Runner'
]


@dataclass
class Alias:
    env: str = 'env'
    gdb: str = 'gdb'


@dataclass
class Runner(Launcher[None]):
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)
    sysroot: str = ''
    alias: Alias = field(default_factory=Alias)

    def run(self) -> list[str]:
        qemu_set_env = [f'{k}={v}' for (k, v) in self.env.items()]
        qemu_set_env = ','.join(qemu_set_env)
        env = {}

        if qemu_set_env:
            env['QEMU_SET_ENV'] = qemu_set_env

        if self.sysroot:
            env['QEMU_LD_PREFIX'] = self.sysroot

        command = []

        if env:
            command += [self.alias.env]

            for k, v in env.items():
                command += [f'{k}={v}']

        command += self.command
        return command

    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[None]:
        with executor.remote(self.run(), redirect=redirect, interactive=bool(redirect)):
            yield


@dataclass
class Debugger(Launcher[None]):
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)
    host: str = ''
    port: int = 1234
    file: str = ''
    sysroot: str = ''
    startup: str = 'target remote {host}:{port}'
    script: str = ''
    alias: Alias = field(default_factory=Alias)

    def __post_init__(self):
        if self.command:
            self.file = self.file if self.file else self.command[0]

    def debug(self) -> list[str]:
        qemu_set_env = [f'{k}={v}' for (k, v) in self.env.items()]
        qemu_set_env = ','.join(qemu_set_env)
        env = {}

        env['QEMU_GDB'] = f'{self.port}'

        if qemu_set_env:
            env['QEMU_SET_ENV'] = qemu_set_env

        if self.sysroot:
            env['QEMU_LD_PREFIX'] = self.sysroot

        command = []

        if env:
            command += [self.alias.env]

            for k, v in env.items():
                command += [f'{k}={v}']

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
