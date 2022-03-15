from abc import ABCMeta, abstractmethod
from typing import Optional


class BaseTransport(ABCMeta):
    @abstractmethod
    def send_bytes(self, payload: bytes) -> None:
        """sends bytes to remote"""

    @abstractmethod
    def receive_bytes(self) -> Optional[bytes]:
        """
        returns bytes from remote
        NOTE: this must never wait, it returns None if
        nothing is avaliable
        """

    @abstractmethod
    def thread_init(self) -> None:
        """
        Some libraries require thread specific context.
        This will be called by the thread once its started
        """


class SenderReceiverPair:
    """To be used by more custom protcols"""

    def __init__(self, sender: BaseTransport, receiver: BaseTransport) -> None:
        self._sender: BaseTransport = sender
        self._receiver: BaseTransport = receiver

    def send_bytes(self, message: bytes) -> None:
        self._sender.send_bytes(message)

    def receive_bytes(self) -> Optional[bytes]:
        """this must never block"""
        return self._receiver.receive_bytes()

    def receiver_init(self) -> None:
        """called by the background thread dealing with the receiver"""
        self._receiver.thread_init()

    def sender_init(self) -> None:
        """called by the background thread dealing with the sender"""
        self._sender.thread_init()
