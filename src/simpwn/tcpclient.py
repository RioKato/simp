from contextlib import suppress
from dataclasses import dataclass
from socket import socket
from ssl import CERT_NONE, PROTOCOL_TLS_CLIENT, SSLContext
from .simp import Client


@dataclass
class TcpClient(Client[socket]):
    host: str
    port: int
    context: SSLContext | None = None

    def __call__(self) -> socket:
        sk = socket()

        try:
            if self.context:
                sk = self.context.wrap_socket(sk)

            while True:
                with suppress(ConnectionError):
                    sk.connect((self.host, self.port))
                    break

            return sk
        except:
            sk.close()
            raise


def unsafeSSL() -> SSLContext:
    context = SSLContext(PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = CERT_NONE
    return context
