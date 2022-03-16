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
