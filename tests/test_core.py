import random
import time
from typing import Iterable
from typing import List

import pytest
from pydantic import ValidationError

import osparc_control
from osparc_control.core import PairedTransmitter
from osparc_control.errors import CommandConfirmationTimeoutError
from osparc_control.errors import CommandNotAcceptedError
from osparc_control.models import CommandManifest
from osparc_control.models import CommandParameter
from osparc_control.models import CommandType

WAIT_FOR_DELIVERY = 0.1

ALL_COMMAND_TYPES: List[CommandType] = [
    CommandType.WITH_DELAYED_REPLY,
    CommandType.WITH_DELAYED_REPLY,
    CommandType.WITHOUT_REPLY,
]

# UTILS


def _get_paired_transmitter(
    local_port: int, remote_port: int, exposed_interface: List[CommandManifest]
) -> PairedTransmitter:
    return PairedTransmitter(
        remote_host="localhost",
        exposed_interface=exposed_interface,
        remote_port=remote_port,
        listen_port=local_port,
    )


# FIXTURES


@pytest.fixture
def paired_transmitter_a() -> Iterable[PairedTransmitter]:
    paired_transmitter = _get_paired_transmitter(1234, 1235, [])
    paired_transmitter.start_background_sync()
    yield paired_transmitter
    paired_transmitter.stop_background_sync()


@pytest.fixture
def mainfest_b() -> List[CommandManifest]:
    add_numbers = CommandManifest(
        action="add_numbers",
        description="adds two numbers",
        params=[
            CommandParameter(name="a", description="param to add"),
            CommandParameter(name="b", description="param to add"),
        ],
        command_type=CommandType.WITH_DELAYED_REPLY,
    )

    get_random = CommandManifest(
        action="get_random",
        description="returns a random number",
        params=[],
        command_type=CommandType.WITH_IMMEDIATE_REPLY,
    )

    greet_user = CommandManifest(
        action="greet_user",
        description="prints the status of the solver",
        params=[CommandParameter(name="name", description="name to greet")],
        command_type=CommandType.WITHOUT_REPLY,
    )

    return [add_numbers, get_random, greet_user]


@pytest.fixture
def paired_transmitter_b(
    mainfest_b: List[CommandManifest],
) -> Iterable[PairedTransmitter]:
    paired_transmitter = _get_paired_transmitter(1235, 1234, mainfest_b)
    paired_transmitter.start_background_sync()
    yield paired_transmitter
    paired_transmitter.stop_background_sync()


@pytest.fixture
def mock_wait_for_received() -> Iterable[None]:
    previous = osparc_control.core.WAIT_FOR_RECEIVED_S
    osparc_control.core.WAIT_FOR_RECEIVED_S = 0.01
    yield
    osparc_control.core.WAIT_FOR_RECEIVED_S = previous


# TESTS


def test_context_manager(mainfest_b: List[CommandManifest]) -> None:
    with _get_paired_transmitter(1235, 1234, mainfest_b):
        pass


def test_request_with_delayed_reply(
    paired_transmitter_a: PairedTransmitter, paired_transmitter_b: PairedTransmitter
) -> None:
    # SIDE A
    request_id = paired_transmitter_a.request_with_delayed_reply(
        "add_numbers", params={"a": 10, "b": 13.3}
    )

    # SIDE B
    wait_for_requests = True
    while wait_for_requests:
        for command in paired_transmitter_b.get_incoming_requests():
            assert command.action == "add_numbers"
            paired_transmitter_b.reply_to_command(
                request_id=command.request_id, payload=sum(command.params.values())
            )
            wait_for_requests = False

    # SIDE A
    time.sleep(WAIT_FOR_DELIVERY)

    has_result, result = paired_transmitter_a.check_for_reply(request_id=request_id)
    assert has_result is True
    assert result is not None


def test_request_with_immediate_reply(
    paired_transmitter_a: PairedTransmitter, paired_transmitter_b: PairedTransmitter
) -> None:
    def _worker_b() -> None:
        count = 1
        wait_for_requests = True
        while wait_for_requests:
            for command in paired_transmitter_b.get_incoming_requests():
                assert command.action == "get_random"
                paired_transmitter_b.reply_to_command(
                    request_id=command.request_id,
                    payload=random.randint(1, 1000),  # noqa: S311
                )
                count += 1

                wait_for_requests = count > 2

    from threading import Thread

    thread = Thread(target=_worker_b, daemon=True)
    thread.start()

    random_integer = paired_transmitter_a.request_with_immediate_reply(
        "get_random", timeout=1.0
    )
    assert type(random_integer) == int
    assert random_integer
    assert 1 <= random_integer <= 1000

    no_reply_in_time = paired_transmitter_a.request_with_immediate_reply(
        "get_random", timeout=0.001
    )
    assert no_reply_in_time is None

    thread.join()


def test_request_without_reply(
    paired_transmitter_a: PairedTransmitter, paired_transmitter_b: PairedTransmitter
) -> None:
    # SIDE A

    paired_transmitter_a.request_without_reply("greet_user", params={"name": "tester"})
    expected_message = "hello tester"

    # SIDE B
    wait_for_requests = True
    while wait_for_requests:
        for command in paired_transmitter_b.get_incoming_requests():
            assert command.action == "greet_user"
            message = f"hello {command.params['name']}"
            assert message == expected_message
            wait_for_requests = False


@pytest.mark.parametrize("command_type", ALL_COMMAND_TYPES)
def test_no_same_action_command_in_exposed_interface(command_type: CommandType) -> None:
    test_command_manifest = CommandManifest(
        action="test", description="test", params=[], command_type=command_type
    )

    with pytest.raises(ValueError):
        _get_paired_transmitter(
            100, 100, [test_command_manifest, test_command_manifest]
        )


def test_no_registered_command(
    paired_transmitter_a: PairedTransmitter, paired_transmitter_b: PairedTransmitter
) -> None:
    with pytest.raises(CommandNotAcceptedError):
        paired_transmitter_a.request_without_reply("command_not_defined")


def test_wrong_command_type(
    paired_transmitter_a: PairedTransmitter, paired_transmitter_b: PairedTransmitter
) -> None:
    with pytest.raises(CommandNotAcceptedError):
        paired_transmitter_a.request_without_reply("add_numbers")


def test_command_params_mismatch(
    paired_transmitter_a: PairedTransmitter, paired_transmitter_b: PairedTransmitter
) -> None:
    with pytest.raises(CommandNotAcceptedError):
        paired_transmitter_a.request_without_reply("add_numbers", {"nope": 123})


def test_side_b_does_not_reply_in_time(mock_wait_for_received: None) -> None:
    paired_transmitter = _get_paired_transmitter(8263, 8263, [])
    paired_transmitter.start_background_sync()
    with pytest.raises(CommandConfirmationTimeoutError):
        paired_transmitter.request_without_reply(
            "no_remote_side_for_command", {"nope": 123}
        )


def test_paired_transmitter_validation() -> None:
    with pytest.raises(ValidationError):
        PairedTransmitter(
            remote_host="localhost",
            exposed_interface=[1],
            remote_port=1,
            listen_port=2,
        )
