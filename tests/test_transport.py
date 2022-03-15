from typing import Iterable, Type

import pytest

from osparc_control.transport.base_transport import BaseTransport, SenderReceiverPair
from osparc_control.transport.in_memory import InMemoryTransport

# UTILS


def _payload_generator(start: int, stop: int) -> Iterable[bytes]:
    assert start < stop
    for k in range(start, stop):
        yield f"test{k}".encode()


# TESTS


@pytest.fixture(params=[InMemoryTransport])
def transport_class(request) -> Type[BaseTransport]:
    return request.param


def test_send_receive(transport_class: Type[BaseTransport]):
    sender_receiver_pair = SenderReceiverPair(
        sender=transport_class("A", "B"),
        receiver=transport_class("B", "A"),
    )

    sender_receiver_pair.receiver_init()
    sender_receiver_pair.sender_init()

    for message in _payload_generator(1, 10):
        # TEST SENDER -> RECEIVER
        sender_receiver_pair.send_bytes(message)
        assert sender_receiver_pair.receive_bytes() == message

    for message in _payload_generator(11, 20):
        # TEST RECEIVER -> SENDER
        sender_receiver_pair.send_bytes(message)
        assert sender_receiver_pair.receive_bytes() == message


def test_receive_returns_none_if_no_message_available():
    receiver = InMemoryTransport("B", "A")
    assert receiver.receive_bytes() is None
