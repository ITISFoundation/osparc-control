from abc import ABCMeta, abstractmethod


class BaseTransport(ABCMeta):
    @abstractmethod
    def send_bytes(self, payload: bytes) -> None:
        """sends bytes to remote"""

    @abstractmethod
    def receive_bytes(self) -> bytes:
        """returns bytes from remote"""
