from itertools import cycle
from string import digits, ascii_letters
from struct import pack, unpack
from typing import Iterator, Literal, Self


INT8_MIN: int = -(1 << 7)
INT16_MIN: int = -(1 << 15)
INT32_MIN: int = -(1 << 31)
INT64_MIN: int = -(1 << 63)
UINT8_MAX: int = (1 << 8) - 1
UINT16_MAX: int = (1 << 16) - 1
UINT32_MAX: int = (1 << 32) - 1
UINT64_MAX: int = (1 << 64) - 1

type ByteOrder = Literal['little', 'big']


def p8(value: int) -> bytes:
    assert (INT8_MIN <= value <= UINT8_MAX)
    return (value & UINT8_MAX).to_bytes(length=1)


def p16(value: int, *, byteorder: ByteOrder = 'little') -> bytes:
    assert (INT16_MIN <= value <= UINT16_MAX)
    return (value & UINT16_MAX).to_bytes(length=2, byteorder=byteorder)


def p32(value: int, *, byteorder: ByteOrder = 'little') -> bytes:
    assert (INT32_MIN <= value <= UINT32_MAX)
    return (value & UINT32_MAX).to_bytes(length=4, byteorder=byteorder)


def p64(value: int, *, byteorder: ByteOrder = 'little') -> bytes:
    assert (INT64_MIN <= value <= UINT64_MAX)
    return (value & UINT64_MAX).to_bytes(length=8, byteorder=byteorder)


def pf(value: float, *, byteorder: ByteOrder = 'little') -> bytes:
    fmt = dict(little='<f', big='>f')
    return pack(fmt[byteorder], value)


def pd(value: float, *, byteorder: ByteOrder = 'little') -> bytes:
    fmt = dict(little='<d', big='>d')
    return pack(fmt[byteorder], value)


def u8(data: bytes, *, signed: bool = False) -> int:
    assert (len(data) == 1)
    return int.from_bytes(data, signed=signed)


def u16(data: bytes, *, signed: bool = False, byteorder: ByteOrder = 'little') -> int:
    assert (len(data) == 2)
    return int.from_bytes(data, signed=signed, byteorder=byteorder)


def u32(data: bytes, *, signed: bool = False, byteorder: ByteOrder = 'little') -> int:
    assert (len(data) == 4)
    return int.from_bytes(data, signed=signed, byteorder=byteorder)


def u64(data: bytes, *, signed: bool = False, byteorder: ByteOrder = 'little') -> int:
    assert (len(data) == 8)
    return int.from_bytes(data, signed=signed, byteorder=byteorder)


def uf(data: bytes, *, byteorder: ByteOrder = 'little') -> int:
    assert (len(data) == 4)
    fmt = dict(little='<f', big='>f')
    return unpack(fmt[byteorder], data)[0]


def ud(data: bytes, *, byteorder: ByteOrder = 'little') -> int:
    assert (len(data) == 8)
    fmt = dict(little='<d', big='>d')
    return unpack(fmt[byteorder], data)[0]


def block(size: int, filler: bytes, *pair: tuple[int, bytes]) -> bytes:
    assert (len(filler) == 1)
    dst = bytearray(filler * size)

    for (i, src) in pair:
        assert (0 <= i <= i + len(src) <= size)
        dst[i:i + len(src)] = src

    return bytes(dst)


class Iota(bytearray):
    def __init__(self):

        super().__init__()
        self.__seed: Iterator[bytes] = cycle(c.encode() for c in digits + ascii_letters)
        self()

    def __call__(self) -> Self:
        self[:] = next(self.__seed)
        return self


iota: Iota = Iota()


def rol64(value: int, n: int) -> int:
    assert (INT64_MIN <= value <= UINT64_MAX)
    assert (-63 <= n <= 63)
    value &= UINT64_MAX

    if 0 <= n:
        value = (value << n) | (value >> (64 - n))
    else:
        value = (value >> (-n)) | (value << (64 + n))

    value &= UINT64_MAX
    return value


def ror64(value: int, n: int) -> int:
    return rol64(value, -n)
