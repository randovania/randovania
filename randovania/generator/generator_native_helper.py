from __future__ import annotations

import dataclasses
import heapq
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Iterable

    from _typeshed import SupportsRichComparison


@dataclasses.dataclass(order=True)
class SearchHeapEntry:
    cost: int
    counter: int
    node: int


class MinPriorityQueue[T: SupportsRichComparison]:
    _data: list[T]

    def __init__(self) -> None:
        self._data = []

    def top(self) -> T:
        return heapq.heappop(self._data)

    def pop(self) -> None:
        # Does nothing, because it assumes it's called immediately after `top`
        pass

    def push(self, value: T) -> None:
        heapq.heappush(self._data, value)

    def empty(self) -> bool:
        return not self._data


class DistancesMapping(typing.Protocol):
    def keys(self) -> Iterable[int]: ...

    def __getitem__(self, item: int) -> int | float: ...

    def __contains__(self, item: int) -> bool: ...
