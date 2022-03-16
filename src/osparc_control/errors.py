from typing import Any, Dict, List
from osparc_control.models import CommandManifest


class BaseControlException(Exception):
    """inherited by all exceptions in this moduls"""


class NoReplyException(BaseControlException):
    """Used when retrying for a result"""


class CommnadNotAcceptedException(BaseControlException):
    """Command was not accepted by remote"""


class NoCommandReceivedArrivedException(BaseControlException):
    """Reply from remote host did not arrive in time"""


class NotAllCommandManifestsHaveHandlersException(Exception):
    def __init__(self, manifests_without_handler: List[CommandManifest]) -> None:
        super().__init__(
            (
                "Not all commands define a handler. Please add one to the "
                f"following {manifests_without_handler} to use this."
            )
        )


class SignatureDoesNotMatchException(Exception):
    def __init__(self, action: str, params: Dict[str, Any]) -> None:
        super().__init__(
            (
                f"Handler signature did not match. Called for action="
                f"'{action}' with params={params}"
            )
        )
