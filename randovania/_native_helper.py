from __future__ import annotations

import collections
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from randovania._native import GraphRequirementSet

T = typing.TypeVar("T")


class VectorProtocol[T](typing.Protocol):
    def size(self) -> int: ...

    def push_back(self, item: T) -> None: ...

    def __getitem__(self, idx: int) -> T: ...

    def __setitem__(self, key: int, value: T) -> None: ...

    def __iter__(self) -> typing.Iterator[T]: ...

    def __len__(self) -> int: ...

    def empty(self) -> bool: ...

    def back(self) -> T: ...

    def pop_back(self) -> None: ...

    def resize(self, count: int, value: T) -> None: ...

    def clear(self) -> None: ...


class Vector[T](list[T]):
    def size(self) -> int:
        return len(self)

    push_back = list.append

    def empty(self) -> bool:
        return not self

    def back(self) -> T:
        return self[-1]

    pop_back = list.pop

    def resize(self, count: int, value: T) -> None:
        self.extend([value] * (count - len(self)))

    def py_resize(self, count: int, factory: Callable[[], T]) -> None:
        self.extend([factory() for _ in range(count - len(self))])

    def __mul__(self, other: typing.SupportsIndex) -> Vector[T]:
        result = Vector[T](list.__mul__(self, other))
        return result

    def __rmul__(self, other: typing.SupportsIndex) -> Vector[T]:
        return self.__mul__(other)


class Deque[T]:
    _data: collections.deque[T]

    def __init__(self) -> None:
        self._data = collections.deque()

    def pop_front(self) -> None:
        self._data.popleft()

    def push_back(self, item: T) -> None:
        self._data.append(item)

    def __getitem__(self, idx: int) -> T:
        return self._data[idx]

    def __setitem__(self, key: int, value: T) -> None:
        self._data[key] = value

    def empty(self) -> bool:
        return not self._data


class UnorderedMap[K, V](dict[K, V]):
    def __iter__(self) -> Iterator[Pair[K, V]]:
        for k, v in self.items():
            yield Pair(k, v)

    def size(self) -> int:
        return len(self)

    def contains(self, key: K) -> bool:
        return key in self

    def empty(self) -> bool:
        return not self


class bitmask_int(int):
    _data: int

    def __init__(self, value: int = 0):
        self._data = value

    def __copy__(self) -> bitmask_int:
        return bitmask_int(self._data)

    def size(self) -> int:
        return 1

    def push_back(self, item: int) -> None:
        raise ValueError("Hardcoded size")

    def __getitem__(self, idx: int) -> int:
        return self._data

    def __setitem__(self, key: int, value: int) -> None:
        self._data = value

    def empty(self) -> bool:
        return self._data == 0

    def back(self) -> int:
        return self._data

    def pop_back(self) -> None:
        raise ValueError("Hardcoded size")

    def resize(self, count: int, value: int) -> None:
        raise ValueError("Hardcoded size")

    def clear(self) -> None:
        raise ValueError("Hardcoded size")

    def __str__(self) -> str:
        return str(self._data)


class PyRef[T: object]:
    def __init__(self, value: T | None = None) -> None:
        self._data = value

    def get(self) -> T | None:
        return self._data

    def set(self, value: T) -> None:
        self._data = value

    def release(self) -> None:
        self._data = None

    def has_value(self) -> bool:
        return self._data is not None

    def __repr__(self):
        return f"PyRef[{self._data!r}]"


class PyImmutableRef[T: object]:
    _data: T

    def __init__(self, value: T) -> None:
        self._data = value

    def get(self) -> T:
        return self._data


def popcount(value: int) -> int:
    """Count the number of set bits in an integer."""
    return bin(value).count("1")


class Pair[T, U]:
    first: T
    second: U

    def __init__(self, first: T, second: U) -> None:
        self.first = first
        self.second = second


class ProcessNodesState:
    checked_nodes: Vector[int]
    nodes_to_check: Deque[int]
    game_states_to_check: Vector[int]
    satisfied_requirement_on_node: Vector[Pair[PyRef[GraphRequirementSet], bool]]

    def __init__(self) -> None:
        self.checked_nodes = Vector[int]()
        self.nodes_to_check = Deque[int]()

        self.game_states_to_check = collections.defaultdict(int)  # type: ignore[assignment]
        self.satisfied_requirement_on_node = collections.defaultdict(  # type: ignore[assignment]
            lambda: Pair(PyRef["GraphRequirementSet"](), False)
        )
