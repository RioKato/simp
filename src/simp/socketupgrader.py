from contextlib import AbstractContextManager, contextmanager, suppress
from multiprocessing import Process, Queue
from os import write
from queue import Empty
from socket import socket
from sys import platform, stderr
from typing import Iterator
from .bufferedsocket import BufferedSocket
from .hexdump import hexdump

if platform.startswith('linux'):
    from os import setpgid
    import readline
else:
    def setpgid(pid: int, pgrp: int, /):
        pass


class SocketMonitor(BufferedSocket, AbstractContextManager):
    def __init__(self, sk: socket, verbose: int):
        super().__init__()
        self.__socket: socket = sk
        self.__verbose: int = verbose
        self.__queue: Queue = Queue()

    def __display(self, data: bytes, header: str):
        message = b''

        if self.__verbose == 1:
            message = data

        if self.__verbose >= 2:
            message = hexdump(data, header).encode()

        write(stderr.fileno(), message)

    def _send(self, data: bytes) -> int:
        n = self.__socket.send(data)
        data = data[:n]
        self.__display(data, '  >')
        return n

    def _recv(self, *, timeout: float = -1) -> bytes:
        block = bool(timeout)
        timeout_ = timeout if timeout > 0 else None

        try:
            return self.__queue.get(block=block, timeout=timeout_)
        except Empty as e:
            if block:
                raise TimeoutError from e
            else:
                raise BlockingIOError from e

    def interactive(self):
        with suppress(KeyboardInterrupt):
            while True:
                data = input().encode()
                self.sendline(data)

    def _transfer(self) -> bool:
        data = self.__socket.recv(0x1000)
        self.__display(data, '    <')
        self.__queue.put(data)
        return bool(data)

    def __exit__(self, *_):
        self.__queue.close()


@contextmanager
def upgrade_socket(connection: socket, *, verbose: int = 1) -> Iterator[SocketMonitor]:
    with SocketMonitor(connection, verbose) as monitor:
        def target():
            setpgid(0, 0)

            while monitor._transfer():
                pass

        proc = Process(target=target)
        proc.start()

        try:
            yield monitor
        finally:
            if proc.is_alive():
                proc.terminate()

            proc.join()
            proc.close()
