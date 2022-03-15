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
    def sender_init(self) -> None:
        """
        Some libraries require thread specific context.
        This will be called by the thread once its started
        """

    @abstractmethod
    def receiver_init(self) -> None:
        """
        Some libraries require thread specific context.
        This will be called by the thread once its started
        """

    def sender_cleanup(self) -> None:
        """
        Some libraries require cleanup when done with them
        """

    def receiver_cleanup(self) -> None:
        """
        Some libraries require cleanup when done with them
        """


class SenderReceiverPair:
    """To be used by more custom protcols"""

    def __init__(self, sender: BaseTransport, receiver: BaseTransport) -> None:
        self._sender: BaseTransport = sender
        self._receiver: BaseTransport = receiver

    def sender_init(self) -> None:
        """called by the background thread dealing with the sender"""
        self._sender.sender_init()

    def send_bytes(self, message: bytes) -> None:
        self._sender.send_bytes(message)

    def receiver_init(self) -> None:
        """called by the background thread dealing with the receiver"""
        self._receiver.receiver_init()

    def receive_bytes(self) -> Optional[bytes]:
        """this must never block"""
        return self._receiver.receive_bytes()

    def sender_cleanup(self) -> None:
        self._sender.sender_cleanup()

    def receiver_cleanup(self) -> None:
        self._receiver.receiver_cleanup()
