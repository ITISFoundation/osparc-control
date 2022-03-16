from typing import Iterable
from typing import Type

import pytest

from osparc_control.transport.base_transport import BaseTransport
from osparc_control.transport.base_transport import SenderReceiverPair
from osparc_control.transport.in_memory import InMemoryTransport
from osparc_control.transport.zeromq import ZeroMQTransport

# UTILS


def _payload_generator(start: int, stop: int) -> Iterable[bytes]:
    assert start < stop
    for k in range(start, stop):
        yield f"test{k}".encode()


# TESTS


@pytest.fixture(params=[InMemoryTransport, ZeroMQTransport])
def transport_class(request) -> Type[BaseTransport]:
    return request.param


@pytest.fixture
def sender_receiver_pair(
    transport_class: Type[BaseTransport],
) -> Iterable[SenderReceiverPair]:
    if transport_class == InMemoryTransport:
        sender = transport_class("A", "B")
        receiver = transport_class("B", "A")
    elif transport_class == ZeroMQTransport:
        port = 1111
        sender = transport_class(
            listen_port=port, remote_host="localhost", remote_port=port
        )
        receiver = transport_class(
            listen_port=port, remote_host="localhost", remote_port=port
        )

    sender_receiver_pair = SenderReceiverPair(sender=sender, receiver=receiver)

    sender_receiver_pair.sender_init()
    sender_receiver_pair.receiver_init()

    yield sender_receiver_pair

    sender_receiver_pair.sender_cleanup()
    sender_receiver_pair.receiver_cleanup()


def test_send_receive_single_thread(sender_receiver_pair: SenderReceiverPair):
    for message in _payload_generator(1, 10):
        print("sending", message)
        sender_receiver_pair.send_bytes(message)

    for expected_message in _payload_generator(1, 10):
        message = sender_receiver_pair.receive_bytes()
        print("received", message)
        assert message == expected_message


def test_receive_nothing(sender_receiver_pair: SenderReceiverPair):
    assert sender_receiver_pair.receive_bytes() is None


def test_receive_returns_none_if_no_message_available():
    receiver = InMemoryTransport("B", "A")
    assert receiver.receive_bytes() is None
