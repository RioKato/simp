from contextlib import suppress
from socket import socket
from ssl import CERT_NONE, PROTOCOL_TLS_CLIENT, SSLContext


def connect(host: str, port: int, context: SSLContext | None = None) -> socket:
    sk = socket()

    try:
        if context:
            sk = context.wrap_socket(sk)

        while True:
            with suppress(ConnectionError):
                sk.connect((host, port))
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
