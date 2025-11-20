from __future__ import annotations

import copy
import typing

T = typing.TypeVar("T")


class Vector[T]:
    _data: list[T]

    def __init__(self) -> None:
        self._data = []

    def __copy__(self) -> Vector[T]:
        result = Vector()
        result._data = copy.copy(self._data)
        return result

    def size(self) -> int:
        return len(self._data)

    def push_back(self, item: T) -> None:
        self._data.append(item)

    def __getitem__(self, idx: int) -> T:
        return self._data[idx]

    def __setitem__(self, key: int, value: T) -> None:
        self._data[key] = value

    def empty(self) -> bool:
        return not self._data

    def back(self) -> T:
        return self._data[-1]

    def pop_back(self) -> None:
        self._data.pop()

    def resize(self, count: int, value: T) -> None:
        self._data.extend(value for _ in range(len(self._data), count))

    def clear(self) -> None:
        self._data.clear()

    def __str__(self) -> str:
        return str(self._data)


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


def popcount(value: int) -> int:
    """Count the number of set bits in an integer."""
    return bin(value).count("1")
