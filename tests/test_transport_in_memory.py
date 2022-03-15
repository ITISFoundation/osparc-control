from typing import Iterable

from osparc_control.transport.in_memory import InMemoryTransport

# UTILS


def _payload_generator(start: int, stop: int) -> Iterable[bytes]:
    assert start < stop
    for k in range(start, stop):
        yield f"test{k}".encode()


# TESTS


def test_send_receive():
    sender = InMemoryTransport("A", "B")
    receiver = InMemoryTransport("B", "A")

    for message in _payload_generator(1, 10):
        # TEST SENDER -> RECEIVER
        sender.send_bytes(message)
        assert receiver.receive_bytes() == message

    for message in _payload_generator(11, 20):
        # TEST RECEIVER -> SENDER
        receiver.send_bytes(message)
        assert sender.receive_bytes() == message


def test_receive_returns_none_if_no_message_available():
    receiver = InMemoryTransport("B", "A")
    assert receiver.receive_bytes() is None
