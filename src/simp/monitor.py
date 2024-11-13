from contextlib import ExitStack, contextmanager, suppress
from multiprocessing import Process
from os import write
from selectors import EVENT_READ, DefaultSelector
from socket import socket, socketpair
from ssl import SSLWantReadError, SSLWantWriteError
from sys import platform, stderr, stdout
from typing import Iterator


class Color:
    @staticmethod
    def __ansi(color: str) -> str:
        return color if stdout.isatty() else ''

    END: str = __ansi('\033[0m')
    BOLD: str = __ansi('\033[1m')
    UNDERLINE: str = __ansi('\033[4m')
    REVERCE: str = __ansi('\033[07m')
    INVISIBLE: str = __ansi('\033[08m')
    BLACK: str = __ansi('\033[30m')
    RED: str = __ansi('\033[31m')
    GREEN: str = __ansi('\033[32m')
    YELLOW: str = __ansi('\033[33m')
    BLUE: str = __ansi('\033[34m')
    PURPLE: str = __ansi('\033[35m')
    CYAN: str = __ansi('\033[36m')
    WHITE: str = __ansi('\033[37m')


def lines(data: bytes) -> Iterator[str]:
    def dumpq(data: bytes) -> str:
        emphasize = [0x0a, 0x55, 0x7f, 0xff]
        text = ''

        for i in range(8):
            if i < len(data):
                b = data[i]

                if b in emphasize:
                    text += f'{Color.GREEN}{b:02x}{Color.END}'
                else:
                    text += f'{b:02x}'
            else:
                text += '  '

        return text

    def dumps(data: bytes) -> str:
        text = bytearray(data)

        for i, b in enumerate(text):
            if not ord(' ') <= b <= ord('~'):
                text[i] = ord('.')

        return text.decode()

    offset = 0

    while data:
        fst, snd, data = data[:8], data[8:16], data[16:]
        left, middle, right = dumpq(fst), dumpq(snd), dumps(fst + snd)
        yield f'{Color.CYAN}[{offset:03x}]{Color.END} {left} {middle} {right}'
        offset += 0x10


def border(char: str) -> str:
    return char * 56


def hexdump(data: bytes, header: str) -> str:
    text = ''

    for line in lines(data):
        text += f'{header} {line}\n'

    if text:
        text = f'{header} {border('-')}\n' + text

    return text


def transfer(dst: socket, src: socket, header: str, verbose: int) -> bool:
    eof = False
    buffer = b''
    dst.setblocking(True)
    src.setblocking(False)

    with suppress(BlockingIOError, SSLWantReadError, SSLWantWriteError):
        while True:
            if data := src.recv(0x1000):
                buffer += data
            else:
                eof = True
                break

    message = b''

    if verbose == 1:
        message = buffer

    if verbose >= 2:
        message = hexdump(buffer, header).encode()

    write(stderr.fileno(), message)

    while buffer:
        n = dst.send(buffer)
        buffer = buffer[n:]

    return eof


class Monitor(Process):
    def __init__(self, external: socket, internal: socket, verbose: int):
        super().__init__()
        self.__external: socket = external
        self.__internal: socket = internal
        self.__verbose: int = verbose

    def run(self):
        if platform == 'linux':
            from os import setpgid

            setpgid(0, 0)

        with DefaultSelector() as selector:
            selector.register(self.__internal, EVENT_READ, lambda: transfer(self.__external, self.__internal, '  >', self.__verbose))
            selector.register(self.__external, EVENT_READ, lambda: transfer(self.__internal, self.__external, '    <', self.__verbose))

            while True:
                for key, _ in selector.select():
                    if key.data():
                        return


@contextmanager
def monitor(external: socket, *, verbose: int = 1) -> Iterator[socket]:
    pair = socketpair()

    with pair[0]:
        with ExitStack() as estack:
            estack.enter_context(pair[1])
            proc = Monitor(external, pair[1], verbose)
            proc.start()
            estack.pop_all().close()

            try:
                yield pair[0]
            finally:
                if proc.is_alive():
                    proc.terminate()

                proc.join()
                proc.close()
