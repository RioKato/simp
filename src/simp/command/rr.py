from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from typing import Callable, Iterator
from .base import Executor, Launcher

__all__ = [
    'Alias', 'Debugger'
]


@dataclass
class Alias:
    gdb: str = 'gdb'
    rr: str = 'rr'
    setarch: str = 'setarch'


class StopRecording(Exception):
    pass


@dataclass
class Debugger(Launcher[Callable[[], None]]):
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

    def record(self) -> list[str]:
        command = []

        if not self.aslr:
            command += [self.alias.setarch, '-R']

        command += [self.alias.rr, 'record']

        for k, v in self.env.items():
            command += ['-v', f'{k}={v}']

        command += self.options
        command += self.command
        return command

    def replay(self) -> list[str]:
        return [self.alias.rr, 'replay', '-s', f'{self.port}']

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
        try:
            with executor.remote(self.record(), redirect=redirect, interactive=bool(redirect)):
                with suppress(StopRecording):
                    def replay():
                        raise StopRecording

                    yield replay
        finally:
            with suppress(KeyboardInterrupt):
                with executor.remote(self.replay(), wait=True):
                    with executor.local(self.cli(), interactive=True, wait=True):
                        pass
