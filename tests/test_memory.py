import pytest

from osparc_control.memory import MemoryStore
from osparc_control.types import AcceptedValues
from osparc_control.errors import (
    CollectionIsFullException,
    KeyIsAlreadyPresent,
    KeyWasNotFoundException,
    TimeIndexMissingException,
    TimeIndexTooSmallOrNotExistingException,
)


@pytest.fixture
def key() -> str:
    return "test_key"


@pytest.fixture
def max_size() -> int:
    return 10


@pytest.fixture
def memory_store() -> MemoryStore:
    return MemoryStore()


@pytest.fixture
def fille_memory_store(
    key: str, memory_store: MemoryStore, max_size: int
) -> MemoryStore:
    memory_store.init_collection(key, max_size)

    for t in range(max_size):
        memory_store.set_value(key, t, f"v{t}")

    return memory_store


def test_memory_store_init_set_get(key: str, memory_store: MemoryStore, max_size: int):
    memory_store.init_collection(key, max_size)

    for t in range(max_size):
        memory_store.set_value(key, t, f"v{t}")

    print(memory_store)

    assert memory_store.get_value(key, 0) == "v0"
    assert memory_store.get_value(key, 9) == "v9"


def test_key_is_not_initialized(key: str, memory_store: MemoryStore):
    with pytest.raises(KeyWasNotFoundException):
        memory_store.get_value(key, 0)


def test_key_is_not_present(key: str, memory_store: MemoryStore):
    with pytest.raises(KeyWasNotFoundException):
        memory_store.set_value(key, 0, "10")


def test_list_is_full(key: str, memory_store: MemoryStore, max_size: int):
    memory_store.init_collection(key, max_size)

    for t in range(max_size):
        memory_store.set_value(key, t, f"v{t}")

    assert memory_store.size_of(key) == max_size

    with pytest.raises(CollectionIsFullException):
        memory_store.set_value(key, 10, f"v10")


def test_initialize_the_same_key_twice_fails(
    key: str, memory_store: MemoryStore, max_size: int
):
    memory_store.init_collection(key, max_size)
    assert key in memory_store._store
    assert key in memory_store._max_sizes

    with pytest.raises(KeyIsAlreadyPresent):
        memory_store.init_collection(key, max_size)


def test_base_values(key: str, memory_store: MemoryStore, max_size: int):
    memory_store.init_collection(key, max_size)

    def _assert_get_is_set(index: float, value: AcceptedValues) -> None:
        memory_store.set_value(key, index, value)
        stored = memory_store.get_value(key, index)
        assert stored == value

    _assert_get_is_set(0, 1)
    _assert_get_is_set(0, 1.0)
    _assert_get_is_set(0, "1")
    _assert_get_is_set(0, b"1")


def test_only_allow_increasing_times(
    key: str, memory_store: MemoryStore, max_size: int
):
    memory_store.init_collection(key, max_size)

    memory_store.set_value(key, 1, "value")

    with pytest.raises(TimeIndexTooSmallOrNotExistingException):
        memory_store.set_value(key, 0, "no_lower_index")


def test_can_update_exiting_times(key: str, memory_store: MemoryStore, max_size: int):
    memory_store.init_collection(key, max_size)

    for k in range(10):
        memory_store.set_value(key, 1, f"can_update_existing{k}")


def test_get_interval(fille_memory_store: MemoryStore, key: str):
    values = fille_memory_store.get_interval(key, 1, 3)
    assert values == [(1, "v1"), (2, "v2")]


def test_get_interval_missing_start_index(fille_memory_store: MemoryStore, key: str):
    with pytest.raises(
        TimeIndexMissingException, match="Provided index 100 was not found"
    ):
        fille_memory_store.get_interval(key, 100, 3)


def test_get_interval_missing_end_index(fille_memory_store: MemoryStore, key: str):
    with pytest.raises(
        TimeIndexMissingException, match="Provided index 200 was not found"
    ):
        fille_memory_store.get_interval(key, 1, 200)
