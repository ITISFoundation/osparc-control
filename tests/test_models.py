import json
from typing import Any, Dict, List, Optional

import pytest
import umsgpack

from osparc_control.models import (
    CommandManifest,
    CommandParameter,
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
        assert CommandManifest.create(
            action="test",
            description="some test action",
            command_type=command_type,
            params=params,
        )


@pytest.mark.parametrize("params", PARAMS)
def test_command(request_id: str, params: Optional[List[CommandParameter]]):
    request_params: Dict[str, Any] = (
        {} if params is None else {x.name: None for x in params}
    )
    command = CommandManifest.create(
        action="test",
        description="some test action",
        command_type=CommnadType.WITHOUT_REPLY,
        params=params,
    )

    assert CommandRequest.from_manifest(
        manifest=command, request_id=request_id, params=request_params
    )


@pytest.mark.parametrize("params", PARAMS)
def test_params_not_respecting_manifest(
    request_id: str, params: Optional[List[CommandParameter]]
):
    command = CommandManifest.create(
        action="test",
        description="some test action",
        command_type=CommnadType.WAIT_FOR_REPLY,
        params=params,
    )

    if params:
        with pytest.raises(ValueError):
            assert CommandRequest.from_manifest(
                manifest=command, request_id=request_id, params={}
            )
    else:
        assert CommandRequest.from_manifest(
            manifest=command, request_id=request_id, params={}
        )


@pytest.mark.parametrize("params", PARAMS)
def test_msgpack_serialization_deserialization(
    request_id: str, params: Optional[List[CommandParameter]]
):

    request_params: Dict[str, Any] = (
        {} if params is None else {x.name: None for x in params}
    )
    manifest = CommandManifest.create(
        action="test",
        description="some test action",
        command_type=CommnadType.WAIT_FOR_REPLY,
        params=params,
    )

    command_request = CommandRequest.from_manifest(
        manifest=manifest, request_id=request_id, params=request_params
    )

    assert command_request == CommandRequest.from_bytes(command_request.to_bytes())

    assert command_request.to_bytes() == umsgpack.packb(
        json.loads(command_request.json())
    )
