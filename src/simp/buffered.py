from contextlib import suppress
from socket import socket
from ssl import SSLWantReadError, SSLWantWriteError
from sys import platform
from typing import Callable


class BufferedSocket:
    def __init__(self, sk: socket):
        self.__sk: socket = sk
        self.__buffer: bytes = b''
        self.__eof: bool = False

    def _send(self, data: bytes) -> int:
        return self.__sk.send(data)

    def _recv(self, *, timeout: float = -1) -> bytes:
        timeout_ = timeout if timeout >= 0 else None
        self.__sk.settimeout(timeout_)
        return self.__sk.recv(0x1000)

    def send(self, data: bytes):
        while data:
            n = self._send(data)
            data = data[n:]

    def sendline(self, data: bytes):
        return self.send(data + b'\n')

    def recv(self, *, size: int = -1, timeout: float = -1) -> bytes:
        if not self.__eof:
            with suppress(BlockingIOError, SSLWantReadError, SSLWantWriteError):
                while data := self._recv(timeout=0):
                    self.__buffer += data

                self.__eof = True

        if not self.__eof and timeout and not self.__buffer:
            if data := self._recv(timeout=timeout):
                self.__buffer += data
            else:
                self.__eof = True

        size = size if size >= 0 else len(self.__buffer)
        data, self.__buffer = self.__buffer[:size], self.__buffer[size:]

        if not self.__eof and size and not data:
            assert (not timeout)
            raise BlockingIOError

        return data

    def __cancel(self, data: bytes):
        self.__buffer = data + self.__buffer

    def recvcond(self, cond: Callable[[bytes], int], *, timeout: float = -1) -> bytes:
        data = b''

        while True:
            try:
                data += self.recv(timeout=timeout)
            except:
                self.__cancel(data)
                raise

            pos = cond(data)

            if pos >= 0:
                data, rest = data[:pos], data[pos:]
                self.__cancel(rest)
                return data

    def recvuntil(self, delim: bytes, *, timeout: float = -1) -> bytes:
        def cond(data: bytes) -> int:
            pos = data.find(delim)

            if pos != -1:
                pos += len(delim)
                return pos
            else:
                return -1

        return self.recvcond(cond, timeout=timeout)

    def recvexact(self, n: int, *, timeout: float = -1) -> bytes:
        def cond(data: bytes) -> int:
            if len(data) >= n:
                return n
            else:
                return -1

        return self.recvcond(cond, timeout=timeout)

    def recvline(self, *, timeout: float = -1) -> bytes:
        return self.recvuntil(b'\n', timeout=timeout)

    def sendafter(self, delim: bytes, data: bytes, *, timeout: float = -1):
        self.recvuntil(delim, timeout=timeout)
        self.send(data)

    def sendlineafter(self, delim: bytes, data: bytes, *, timeout: float = -1):
        self.recvuntil(delim, timeout=timeout)
        self.sendline(data)

    def interactive(self):
        if platform == 'linux':
            import readline

        with suppress(KeyboardInterrupt):
            while True:
                data = input().encode()
                self.sendline(data)
