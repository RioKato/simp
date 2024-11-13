from abc import ABCMeta, abstractmethod
from contextlib import AbstractContextManager, ExitStack, contextmanager, nullcontext
from typing import Iterator


class Executor[Redirect](metaclass=ABCMeta):
    @abstractmethod
    @contextmanager
    def local(self, command: list[str], *, redirect: Redirect | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        ...

    @abstractmethod
    @contextmanager
    def remote(self, command: list[str], *, redirect: Redirect | None = None, interactive: bool = False, tracable: bool = False, wait: bool = False) -> Iterator[int]:
        ...


class Launcher[Helper](metaclass=ABCMeta):
    @abstractmethod
    @contextmanager
    def __call__[Redirect](self, executor: Executor[Redirect], *, redirect: Redirect | None = None) -> Iterator[Helper]:
        ...


class Bridge[Connection, Redirect](metaclass=ABCMeta):
    @abstractmethod
    def __call__(self) -> tuple[Connection, Redirect]:
        ...


@contextmanager
def run[Helper, Connection: AbstractContextManager, Redirect: AbstractContextManager](
        launcher: Launcher[Helper],
        executor: Executor[Redirect],
        bridge: Bridge[Connection, Redirect] | None) -> Iterator[tuple[Helper, Connection | None]]:

    if bridge:
        connection, redirect = bridge()
    else:
        connection, redirect = None, None

    with connection if connection else nullcontext():
        with ExitStack() as estack:
            if redirect:
                estack.enter_context(redirect)

            with launcher(executor, redirect=redirect) as helper:
                estack.pop_all().close()
                yield (helper, connection)
