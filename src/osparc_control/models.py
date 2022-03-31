from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

import umsgpack  # type: ignore
from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field
from pydantic import PrivateAttr
from pydantic import validator


class CommandBase(BaseModel):
    def to_bytes(self) -> bytes:
        return umsgpack.packb(self.dict())  # type: ignore

    @classmethod
    def from_bytes(cls, raw: bytes) -> Optional[Any]:
        return cls.parse_obj(umsgpack.unpackb(raw))

    class Config:
        extra = Extra.allow


class CommandParameter(BaseModel):
    name: str = Field(
        ..., description="name of the parameter to be provided with the commnad"
    )
    description: str = Field(
        ...,
        description=(
            "provide more information to the user, how this command should be used"
        ),
    )


class CommandType(str, Enum):
    # the command expects no reply
    WITHOUT_REPLY = "WITHOUT_REPLY"

    # the command will provide a reply
    # the user is require to check for the results
    # of this reply
    WITH_DELAYED_REPLY = "WITH_DELAYED_REPLY"

    # the command will return the result immediately
    # and user code will be blocked until reply arrives
    # used for very fast replies (provide data which already exists)
    WITH_IMMEDIATE_REPLY = "WITH_IMMEDIATE_REPLY"


class CommandManifest(BaseModel):
    # used to speed up parameter matching
    _params_names_set: Set[str] = PrivateAttr()

    action: str = Field(..., description="name of the action to be triggered on remote")
    description: str = Field(..., description="more details about the action")
    params: List[CommandParameter] = Field(
        None, description="requested parameters by the user"
    )
    command_type: CommandType = Field(
        ..., description="describes the command type, behaviour and usage"
    )

    @validator("params")
    @classmethod
    def ensure_unique_parameter_names(
        cls, v: List[CommandParameter]
    ) -> List[CommandParameter]:
        if len(v) != len({x.name for x in v}):
            raise ValueError(f"Duplicate CommandParameter name found in {v}")
        return v


class CommandRequest(CommandBase):
    request_id: str = Field(..., description="unique identifier")
    action: str = Field(..., description="name of the action to be triggered on remote")
    params: Dict[str, Any] = Field({}, description="requested parameters by the user")
    command_type: CommandType = Field(
        ..., description="describes the command type, behaviour and usage"
    )


class CommandReceived(CommandBase):
    request_id: str = Field(..., description="unique identifier from request")
    accepted: bool = Field(
        ..., description="True if command is correctly formatted otherwise False"
    )
    error_message: Optional[str] = Field(
        None,
        description=(
            "A mesage displayed to the user in case something went wrong. "
            "Will always be present if accepted=False"
        ),
    )

    @validator("error_message")
    @classmethod
    def error_message_present_if_not_accepted(
        cls, v: str, values: Dict[str, Any]
    ) -> Optional[str]:
        if values["accepted"] is False and v is None:
            raise ValueError("error_message must not be None when accepted is False")

        if values["accepted"] is True and v is not None:
            raise ValueError("error_message must be None when accepted is True")
        return v


class CommandReply(CommandBase):
    reply_id: str = Field(..., description="unique identifier from request")
    payload: Any = Field(..., description="user defined value for the command")


class TrackedRequest(BaseModel):
    request: CommandRequest = Field(..., description="request being tracked")
    reply: Optional[CommandReply] = Field(
        None, description="reply will be not None if received"
    )


RequestsTracker = Dict[str, TrackedRequest]
