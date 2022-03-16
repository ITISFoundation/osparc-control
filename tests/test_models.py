import json
from typing import Any, Dict, List, Optional

import pytest
import umsgpack

from osparc_control.models import (
    CommandManifest,
    CommandParameter,
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
            handler=None,
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
        handler=None,
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
        handler=None,
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
