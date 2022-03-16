class BaseControlError(Exception):
    """inherited by all exceptions in this module"""


class NoReplyError(BaseControlError):
    """Used when retrying for a result"""


class CommnadNotAcceptedError(BaseControlError):
    """Command was not accepted by remote"""


class NoCommandReceivedArrivedError(BaseControlError):
    """Reply from remote host did not arrive in time"""
