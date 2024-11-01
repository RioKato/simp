from sys import stdout
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
