from __future__ import annotations

from typing import Self


class PickupIndex:
    __slots__ = ("_index",)
    _index: int

    @property
    def long_name(self) -> str:
        return f"PickupIndex {self._index}"

    @property
    def short_name(self) -> str:
        return self.long_name

    def __init__(self, index: int):
        self._index = index

    def __lt__(self, other: PickupIndex) -> bool:
        return self._index < other._index

    def __repr__(self) -> str:
        return self.long_name

    def __hash__(self) -> int:
        return self._index

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PickupIndex) and other._index == self._index

    @property
    def index(self) -> int:
        return self._index

    @property
    def as_json(self) -> int:
        return self._index

    @classmethod
    def from_json(cls, value: int) -> Self:
        return cls(value)
