from typing import Optional
from tenacity import RetryError, Retrying
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_fixed

import zmq

from .base_transport import BaseTransport


class ZeroMQTransport(metaclass=BaseTransport):
    def __init__(self, listen_port: int, remote_host: str, remote_port: int):
        self.listen_port: int = listen_port
        self.remote_host: str = remote_host
        self.remote_port: int = remote_port

        self._recv_socket: Optional[zmq.socket.Socket] = None
        self._send_socket: Optional[zmq.socket.Socket] = None
        self._send_contex: Optional[zmq.context.Context] = None
        self._recv_contex: Optional[zmq.context.Context] = None

    def send_bytes(self, payload: bytes) -> None:
        assert self._send_socket

        self._send_socket.send(payload)

    def receive_bytes(
        self, retry_count: int = 3, wait_between: float = 0.01
    ) -> Optional[bytes]:
        assert self._recv_socket

        # try to fetch a message, usning unlocking sockets does not guarantee
        # that data is always present, retry 3 times in a short amount of time
        # this will guarantee the message arrives
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(retry_count), wait=wait_fixed(wait_between)
            ):
                with attempt:
                    message: bytes = self._recv_socket.recv(zmq.NOBLOCK)
                    return message
        except RetryError:
            return None

    def sender_init(self) -> None:
        self._send_contex = zmq.Context()
        self._send_socket = self._send_contex.socket(zmq.PUSH)
        self._send_socket.bind(f"tcp://*:{self.listen_port}")

    def receiver_init(self) -> None:
        self._recv_contex = zmq.Context()
        self._recv_socket = self._recv_contex.socket(zmq.PULL)
        self._recv_socket.connect(f"tcp://{self.remote_host}:{self.remote_port}")

    def sender_cleanup(self) -> None:
        assert self._send_socket
        self._send_socket.close()
        assert self._send_contex
        self._send_contex.term()

    def receiver_cleanup(self) -> None:
        assert self._recv_socket
        self._recv_socket.close()
        assert self._recv_contex
        self._recv_contex.term()
