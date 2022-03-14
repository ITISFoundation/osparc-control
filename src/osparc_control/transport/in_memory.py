from typing import Dict
from queue import Queue

from .base_transport import BaseTransport


class InMemoryTransport(metaclass=BaseTransport):
    """
    Blocking in memory implementation, working with queues.
    Can only be mixed with threading.

    - sends data to `destination`
    - fetches data from `source`
    """

    _SHARED_QUEUES: Dict[str, Queue] = {}

    def __init__(self, source: str, destination: str):
        self.source: str = source
        self.destination: str = destination

        self._SHARED_QUEUES[self.source] = Queue()
        self._SHARED_QUEUES[self.destination] = Queue()

    def send_bytes(self, payload: bytes) -> None:
        self._SHARED_QUEUES[self.destination].put(payload)

    def receive_bytes(self) -> bytes:
        return self._SHARED_QUEUES[self.source].get()
