class BaseControlError(Exception):
    """inherited by all exceptions in this module"""


class NoReplyError(BaseControlError):
    """Used when retrying for a result"""


class CommandNotAcceptedError(BaseControlError):
    """Command was not accepted by remote"""


class CommandConfirmationTimeoutError(BaseControlError):
    """Reply from remote host did not arrive in time"""
