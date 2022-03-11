from typing import Dict, Union, List, Tuple
from collections import OrderedDict
from .types import AcceptedValues
from .errors import (
    CollectionIsFullException,
    KeyIsAlreadyPresent,
    KeyWasNotFoundException,
    TimeIndexMissingException,
    TimeIndexTooSmallOrNotExistingException,
)


class MemoryStore:
    """Size limited time indexed memory store"""

    def __init__(self) -> None:
        self._store: Dict[str, OrderedDict[float, AcceptedValues]] = {}
        self._max_sizes: Dict[str, int] = {}
        self._last_inserted_time_index: Dict[str, float] = {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self._store} {self._max_sizes}>"

    def _ensure_key(self, key: str) -> None:
        if key not in self._store:
            raise KeyWasNotFoundException(f"Key {key} was not found")

    def init_collection(self, key: str, max_size: int) -> None:
        if key in self._store:
            raise KeyIsAlreadyPresent(key, self._store[key])

        self._store[key] = OrderedDict()
        self._max_sizes[key] = max_size

    def set_value(self, key: str, time_index: float, value: AcceptedValues) -> None:
        self._ensure_key(key)

        # ensure new previous times are not inserter
        # it is ok to change their values but not to add new ones
        last_inserted_time_index = self._last_inserted_time_index.get(
            key, -float("inf")
        )
        if last_inserted_time_index > time_index and time_index not in self._store[key]:
            raise TimeIndexTooSmallOrNotExistingException(
                time_index, last_inserted_time_index
            )

        self._store[key][time_index] = value
        self._last_inserted_time_index[key] = time_index

        # collection is size limited, avoid memory blow up, user is required
        # to specify the size before using it
        if len(self._store[key]) > self._max_sizes[key]:
            raise CollectionIsFullException(key=key, max_items=self._max_sizes[key])

    def size_of(self, key: str) -> int:
        self._ensure_key(key)
        return len(self._store[key])

    def get_value(
        self, key: str, time_index: float, default: Union[AcceptedValues, None] = None
    ) -> Union[AcceptedValues, None]:
        # maybe this should raise if time_index is missing?
        self._ensure_key(key)

        return self._store[key].get(time_index, default)

    def get_interval(
        self, key: str, time_index_start: float, time_index_stop: float
    ) -> List[Tuple[float, AcceptedValues]]:
        """works exactly like list slicing"""
        self._ensure_key(key)

        collection: OrderedDict[float, AcceptedValues] = self._store[key]

        if time_index_start not in collection:
            raise TimeIndexMissingException(time_index_start)

        if time_index_stop not in collection:
            raise TimeIndexMissingException(time_index_stop)

        # map key_index to order than you search for them
        key_to_index = {key: i for i, key in enumerate(collection.keys())}

        start_index = key_to_index[time_index_start]
        stop_index = key_to_index[time_index_stop]

        collection_items = list(collection.items())

        return collection_items[start_index:stop_index]
