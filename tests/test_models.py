import json
from typing import Any, Dict, List, Optional

import pytest
import umsgpack
from pydantic import ValidationError

from osparc_control.models import (
    CommandManifest,
    CommandParameter,
    CommandReceived,
    CommandReply,
    CommandRequest,
    CommnadType,
)


@pytest.fixture
def request_id() -> str:
    return "unique_id"


PARAMS: List[Optional[List[CommandParameter]]] = [
    None,
    [],
    [CommandParameter(name="first_arg", description="the first arg description")],
]


@pytest.mark.parametrize("params", PARAMS)
def test_command_manifest(params: Optional[List[CommandParameter]]):
    for command_type in CommnadType:
        assert CommandManifest(
            action="test",
            description="some test action",
            command_type=command_type,
            params=[] if params is None else params,
        )


@pytest.mark.parametrize("params", PARAMS)
def test_command(request_id: str, params: Optional[List[CommandParameter]]):
    request_params: Dict[str, Any] = (
        {} if params is None else {x.name: None for x in params}
    )
    manifest = CommandManifest(
        action="test",
        description="some test action",
        command_type=CommnadType.WITHOUT_REPLY,
        params=[] if params is None else params,
    )

    assert CommandRequest(
        request_id=request_id,
        action=manifest.action,
        command_type=manifest.command_type,
        params=request_params,
    )


@pytest.mark.parametrize("params", PARAMS)
def test_msgpack_serialization_deserialization(
    request_id: str, params: Optional[List[CommandParameter]]
):

    request_params: Dict[str, Any] = (
        {} if params is None else {x.name: None for x in params}
    )
    manifest = CommandManifest(
        action="test",
        description="some test action",
        command_type=CommnadType.WAIT_FOR_REPLY,
        params=[] if params is None else params,
    )

    command_request = CommandRequest(
        request_id=request_id,
        action=manifest.action,
        command_type=manifest.command_type,
        params=request_params,
    )

    assert command_request == CommandRequest.from_bytes(command_request.to_bytes())

    assert command_request.to_bytes() == umsgpack.packb(
        json.loads(command_request.json())
    )


@pytest.mark.parametrize("payload", [None, "a_string", 1, 1.0, b"some_bytes"])
def test_command_reply_payloads_serialization_deserialization(
    request_id: str, payload: Any
):
    command_reply = CommandReply(reply_id=request_id, payload=payload)
    assert command_reply
    assert command_reply == CommandReply.from_bytes(command_reply.to_bytes())


def test_command_accepted_ok(request_id: str):
    assert CommandReceived(request_id=request_id, accepted=True, error_message=None)
    assert CommandReceived(
        request_id=request_id, accepted=False, error_message="some error"
    )


def test_command_accepted_fails(request_id: str):
    with pytest.raises(ValidationError):
        assert CommandReceived(
            request_id=request_id, accepted=False, error_message=None
        )
    with pytest.raises(ValidationError):
        assert CommandReceived(
            request_id=request_id, accepted=True, error_message="some error"
        )


def test_duplicate_command_parameter_name_in_manifest():
    with pytest.raises(ValidationError):
        CommandManifest(
            action="test",
            description="with invalid paramters",
            params=[
                CommandParameter(name="a", description="ok"),
                CommandParameter(name="a", description="not allowed same name"),
            ],
            command_type=CommnadType.WITH_REPLAY,
        )
