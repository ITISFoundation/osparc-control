from collections import OrderedDict


class BaseControlException(Exception):
    """inherited by all exceptions in this moduls"""


class CollectionIsFullException(BaseControlException):
    """no more elements could be added to the list"""

    def __init__(self, key: str, max_items: int) -> None:
        super().__init__(f"Current size of {key} exceeds {max_items}")


class KeyWasNotFoundException(BaseControlException):
    def __init__(self, key: str) -> None:
        super().__init__(f"Key {key} was not found")


class KeyIsAlreadyPresent(BaseControlException):
    def __init__(self, key: str, data: OrderedDict) -> None:
        super().__init__(f"Key {key} is already present with data {data}")


class TimeIndexTooSmallOrNotExistingException(BaseControlException):
    def __init__(self, time_index: float, last_inserted_time_index: float) -> None:
        message = (
            f"Trying to insert time={time_index} which is: "
            f"grater than last inserted time={last_inserted_time_index} and "
            f"not a previously existing value."
        )
        super().__init__(message)


class TimeIndexMissingException(BaseControlException):
    def __init__(self, time_index: float) -> None:
        super().__init__(f"Provided index {time_index} was not found")
