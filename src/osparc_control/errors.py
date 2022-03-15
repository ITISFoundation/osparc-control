class BaseControlException(Exception):
    """inherited by all exceptions in this moduls"""


class NoReplyException(BaseControlException):
    """Used when retrying for a result"""
