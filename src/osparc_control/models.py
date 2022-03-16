from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import umsgpack
from pydantic import BaseModel, Extra, Field, validator


class CommandBase(BaseModel):
    def to_bytes(self) -> bytes:
        return umsgpack.packb(self.dict())

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
        description="provide more information to the user, how this command should be used",
    )


class CommnadType(str, Enum):
    # NOTE: ANE -> KZ: can you please let me know if names and descriptions make sense?
    # please suggest better ones

    # no reply is expected for this command
    # nothing will be awaited
    WITHOUT_REPLY = "WITHOUT_REPLY"

    # a reply is expected and the user must check
    # for the results
    WITH_REPLAY = "WITH_REPLAY"

    # user requests a parameter that he would like to have
    # immediately, the request will be blocked until
    # a value is returned
    WAIT_FOR_REPLY = "WAIT_FOR_REPLY"


class CommandManifest(BaseModel):
    action: str = Field(..., description="name of the action to be triggered on remote")
    description: str = Field(..., description="more details about the action")
    params: List[CommandParameter] = Field(
        None, description="requested parameters by the user"
    )
    command_type: CommnadType = Field(
        ..., description="describes the command type, behaviour and usage"
    )
    handler: Optional[Callable] = Field(
        None,
        description=(
            "if the user provides a callable it will be called to handle"
            "incoming requests"
        ),
    )


class CommandRequest(CommandBase):
    request_id: str = Field(..., description="unique identifier")
    action: str = Field(..., description="name of the action to be triggered on remote")
    params: Dict[str, Any] = Field({}, description="requested parameters by the user")
    command_type: CommnadType = Field(
        ..., description="describes the command type, behaviour and usage"
    )


class CommandAccepted(CommandBase):
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
