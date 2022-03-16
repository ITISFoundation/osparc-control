import random
import time
from typing import Iterable
from typing import List

import pytest

from osparc_control.core import ControlInterface
from osparc_control.models import CommandManifest
from osparc_control.models import CommandParameter
from osparc_control.models import CommnadType

WAIT_FOR_DELIVERY = 0.01


def _get_control_interface(
    local_port: int, remote_port: int, exposed_interface: List[CommandManifest]
) -> ControlInterface:
    return ControlInterface(
        remote_host="localhost",
        exposed_interface=exposed_interface,
        remote_port=remote_port,
        listen_port=local_port,
    )


@pytest.fixture
def control_interface_a() -> Iterable[ControlInterface]:
    control_interface = _get_control_interface(1234, 1235, [])
    control_interface.start_background_sync()
    yield control_interface
    control_interface.stop_background_sync()


@pytest.fixture
def mainfest_b() -> List[CommandManifest]:
    add_numbers = CommandManifest(
        action="add_numbers",
        description="adds two numbers",
        params=[
            CommandParameter(name="a", description="param to add"),
            CommandParameter(name="b", description="param to add"),
        ],
        command_type=CommnadType.WITH_DELAYED_REPLY,
    )

    get_random = CommandManifest(
        action="get_random",
        description="returns a random number",
        params=[],
        command_type=CommnadType.WITH_IMMEDIATE_REPLY,
    )

    greet_user = CommandManifest(
        action="greet_user",
        description="prints the status of the solver",
        params=[CommandParameter(name="name", description="name to greet")],
        command_type=CommnadType.WITHOUT_REPLY,
    )

    return [add_numbers, get_random, greet_user]


@pytest.fixture
def control_interface_b(
    mainfest_b: List[CommandManifest],
) -> Iterable[ControlInterface]:
    control_interface = _get_control_interface(1235, 1234, mainfest_b)
    control_interface.start_background_sync()
    yield control_interface
    control_interface.stop_background_sync()


def test_request_with_delayed_reply(
    control_interface_a: ControlInterface, control_interface_b: ControlInterface
) -> None:
    # SIDE A
    request_id = control_interface_a.request_with_delayed_reply(
        "add_numbers", params={"a": 10, "b": 13.3}
    )

    # SIDE B
    wait_for_requests = True
    while wait_for_requests:
        for command in control_interface_b.get_incoming_requests():
            assert command.action == "add_numbers"
            control_interface_b.reply_to_command(
                request_id=command.request_id, payload=sum(command.params.values())
            )
            wait_for_requests = False

    # SIDE A
    time.sleep(WAIT_FOR_DELIVERY)

    has_result, result = control_interface_a.check_for_reply(request_id=request_id)
    assert has_result is True
    assert result is not None


def test_request_with_immediate_reply(
    control_interface_a: ControlInterface, control_interface_b: ControlInterface
) -> None:
    def _worker_b() -> None:
        wait_for_requests = True
        while wait_for_requests:
            for command in control_interface_b.get_incoming_requests():
                assert command.action == "get_random"
                control_interface_b.reply_to_command(
                    request_id=command.request_id,
                    payload=random.randint(1, 1000),  # noqa: S311
                )
                wait_for_requests = False

    from threading import Thread

    thread = Thread(target=_worker_b, daemon=True)
    thread.start()

    random_integer = control_interface_a.request_with_immediate_reply(
        "get_random", timeout=1.0
    )
    assert type(random_integer) == int
    assert random_integer
    assert 1 <= random_integer <= 1000

    thread.join()


def test_request_without_reply(
    control_interface_a: ControlInterface, control_interface_b: ControlInterface
) -> None:
    # SIDE A

    control_interface_a.request_without_reply("greet_user", params={"name": "tester"})
    expected_message = "hello tester"

    # SIDE B
    wait_for_requests = True
    while wait_for_requests:
        for command in control_interface_b.get_incoming_requests():
            assert command.action == "greet_user"
            message = f"hello {command.params['name']}"
            assert message == expected_message
            wait_for_requests = False
