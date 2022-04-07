from typing import Optional

import zmq
from tenacity import RetryError
from tenacity import Retrying
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_fixed
from zmq import Context
from zmq import Socket

from .base_transport import BaseTransport

RETRY_COUNT: int = 3
WAIT_BETWEEN: float = 0.01


class ZeroMQTransport(BaseTransport):
    def __init__(self, listen_port: int, remote_host: str, remote_port: int):
        self.listen_port: int = listen_port
        self.remote_host: str = remote_host
        self.remote_port: int = remote_port

        self._recv_socket: Optional[Socket] = None
        self._send_socket: Optional[Socket] = None
        self._send_contex: Optional[Context] = None
        self._recv_contex: Optional[Context] = None

    def send_bytes(self, payload: bytes) -> None:
        assert self._send_socket  # noqa: S101

        self._send_socket.send(payload)  # type: ignore

    def receive_bytes(self) -> Optional[bytes]:
        assert self._recv_socket  # noqa: S101

        # try to fetch a message, using blocking sockets does not guarantee
        # that data is always present, retry 3 times in a short amount of time
        # this will guarantee the message arrives
        message: Optional[bytes] = None
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(RETRY_COUNT), wait=wait_fixed(WAIT_BETWEEN)
            ):
                with attempt:
                    message = self._recv_socket.recv(zmq.NOBLOCK)  # type: ignore
        except RetryError:
            pass

        return message

    def sender_init(self) -> None:
        self._send_contex = zmq.Context()  # type: ignore
        self._send_socket = self._send_contex.socket(zmq.PUSH)  # type: ignore
        self._send_socket.bind(f"tcp://*:{self.listen_port}")  # type: ignore

    def receiver_init(self) -> None:
        self._recv_contex = zmq.Context()  # type: ignore
        self._recv_socket = self._recv_contex.socket(zmq.PULL)  # type: ignore
        self._recv_socket.connect(  # type: ignore
            f"tcp://{self.remote_host}:{self.remote_port}"
        )

    def sender_cleanup(self) -> None:
        assert self._send_socket  # noqa: S101
        self._send_socket.close()  # type: ignore
        assert self._send_contex  # noqa: S101
        self._send_contex.term()  # type: ignore

    def receiver_cleanup(self) -> None:
        assert self._recv_socket  # noqa: S101
        self._recv_socket.close()  # type: ignore
        assert self._recv_contex  # noqa: S101
        self._recv_contex.term()  # type: ignore
