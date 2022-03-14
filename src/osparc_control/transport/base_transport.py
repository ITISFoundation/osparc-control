from abc import ABCMeta, abstractmethod


class BaseTransport(ABCMeta):
    @abstractmethod
    def send_bytes(self, payload: bytes) -> None:
        """sends bytes to remote"""

    @abstractmethod
    def receive_bytes(self) -> bytes:
        """returns bytes from remote"""


class SenderReceiverPair:
    """To be used by more custom protcols"""

    def __init__(self, sender: BaseTransport, receiver: BaseTransport) -> None:
        self._sender: BaseTransport = sender
        self._receiver: BaseTransport = receiver

    def send_bytes(self, message: bytes) -> None:
        self._sender.send_bytes(message)

    def receive_bytes(self) -> bytes:
        return self._receiver.receive_bytes()
