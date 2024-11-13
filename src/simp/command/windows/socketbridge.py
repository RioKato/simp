from contextlib import AbstractContextManager, contextmanager
from ctypes import POINTER, Structure, WinDLL, WinError, c_byte, c_char, c_char_p, c_int, c_long, c_short, c_uint, c_ulong, c_ushort, c_void_p, pointer, sizeof
from ctypes.wintypes import DWORD, WORD
from dataclasses import dataclass
from socket import AF_INET, SOCK_STREAM, htons, inet_aton, socket
from typing import Iterator
from ..base import Bridge


WSADESCRIPTION_LEN = 256
WSASYS_STATUS_LEN = 128


class WSADATA(Structure):
    _fields_ = [
        ('wVersion', WORD),
        ('wHighVersion', WORD),
        ('szDescription', c_char * (WSADESCRIPTION_LEN + 1)),
        ('szSystemStatus', c_char * (WSASYS_STATUS_LEN + 1)),
        ('iMaxSockets', c_ushort),
        ('iMaxUdpDg', c_ushort),
        ('lpVendorInfo', c_char_p),
    ]


class sockaddr_in(Structure):
    _fields_ = [
        ('sin_family', c_short),
        ('sin_port', c_ushort),
        ('sin_addr', c_byte * 4),
        ('sin_zero', c_char * 8)
    ]


class Ws2:
    ws2_32 = WinDLL('ws2_32')

    LPWSADATA = POINTER(WSADATA)
    WSAStartup = ws2_32.WSAStartup
    WSAStartup.argtypes = [WORD, LPWSADATA]
    WSAStartup.restype = c_int

    WSACleanup = ws2_32.WSACleanup
    WSACleanup.argtypes = []
    WSACleanup.restype = c_int

    INVALID_SOCKET: int = 0xffffffff
    SOCKET = c_uint
    GROUP = c_uint
    WSASocket = ws2_32.WSASocketA
    WSASocket.argtypes = [c_int, c_int, c_int, c_void_p, GROUP, DWORD]
    WSASocket.restype = SOCKET

    closesocket = ws2_32.closesocket
    closesocket.argtypes = [SOCKET]
    closesocket.restype = c_int

    WSAGetLastError = ws2_32.WSAGetLastError
    WSAGetLastError.argtypes = []
    WSAGetLastError.restype = c_int

    connect = ws2_32.connect
    connect.argtypes = [SOCKET, POINTER(sockaddr_in), c_int]
    connect.restype = c_int

    FIOBIO: int = 0x8004667e
    ioctlsocket = ws2_32.ioctlsocket
    ioctlsocket.argtypes = [SOCKET, c_long, POINTER(c_ulong)]
    ioctlsocket.restype = c_int


@contextmanager
def WSAStartup() -> Iterator[None]:
    wsadata = WSADATA()
    err = Ws2.WSAStartup(0x0202, Ws2.LPWSADATA(wsadata))

    if err != 0:
        raise WinError(err)

    try:
        yield
    finally:
        err = Ws2.WSACleanup()

        if err != 0:
            raise WinError(Ws2.WSAGetLastError())


class WinSocket(AbstractContextManager):
    def __init__(self, handle: int):
        self.__handle: int = handle

    def close(self):
        if self.__handle >= 0:
            Ws2.closesocket(self.__handle)

        self.__handle = -1

    def fileno(self) -> int:
        return self.__handle

    def __exit__(self, *_):
        self.close()


@dataclass
class SocketBridge(Bridge[socket, WinSocket]):
    localhost: str = '127.0.0.1'

    def __call__(self) -> tuple[socket, WinSocket]:
        with socket() as listener:
            listener.bind((self.localhost, 0))
            listener.listen(1)
            host, port = listener.getsockname()
            winsocket = Ws2.WSASocket(AF_INET, SOCK_STREAM, 0, None, 0, 0)
            winsocket = WinSocket(winsocket)

            if winsocket.fileno() == Ws2.INVALID_SOCKET:
                raise WinError(Ws2.WSAGetLastError())

            if Ws2.ioctlsocket(winsocket.fileno(), Ws2.FIOBIO, pointer(c_ulong(1))):
                raise WinError(Ws2.WSAGetLastError())

            sockaddr = sockaddr_in()
            sockaddr.sin_family = AF_INET
            sockaddr.sin_addr = tuple(inet_aton(host))
            sockaddr.sin_port = htons(port)
            Ws2.connect(winsocket.fileno(), pointer(sockaddr), sizeof(sockaddr_in))

            try:
                accepted, _ = listener.accept()
            except:
                winsocket.close()
                raise

        if Ws2.ioctlsocket(winsocket.fileno(), Ws2.FIOBIO, pointer(c_ulong(0))):
            winsocket.close()
            accepted.close()
            raise WinError(Ws2.WSAGetLastError())

        return (accepted, winsocket)
