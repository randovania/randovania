from __future__ import annotations


class Path(tuple[int, ...]):
    __slots__ = ()

    def row(self) -> int:
        return self[-1]

    def parent(self) -> Path:
        return Path(self[:-1])

    def head(self) -> int:
        return self[0]

    def tail(self) -> Path:
        return Path(self[1:])

    def extend_with(self, idx: int) -> Path:
        return Path((*self, idx))

    def prefixed_with(self, idx: int) -> Path:
        return Path((idx, *self))

    def reversed(self) -> Path:
        return Path(self[::-1])

    def next_sibling(self) -> Path:
        return Path((*self[:-1], self[-1] + 1))

    def previous_sibling(self) -> Path:
        return Path((*self[:-1], self[-1] - 1))
