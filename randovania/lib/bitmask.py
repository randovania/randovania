# distutils: language=c++
# cython: profile=False
# pyright: reportPossiblyUnboundVariable=false
# pyright: reportReturnType=false
# mypy: disable-error-code="return"

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    # The package is named `Cython`, so in a case-sensitive system mypy fails to find cython with just `import cython`
    import Cython as cython
else:
    # However cython's compiler seems to expect the import to be this way, otherwise `cython.compiled` breaks
    import cython


if cython.compiled:
    if not typing.TYPE_CHECKING:
        from cython.cimports.libcpp.vector import vector
        from cython.cimports.randovania.lib.bitmask import BitmaskData
        from cython.cimports.randovania.lib.cython_helper import pool
else:
    if typing.TYPE_CHECKING:
        from randovania.lib.cython_helper import Vector as vector

    def pool() -> typing.NoReturn:
        raise NotImplementedError  # unused; exists only for mypy


def pool_diagnostics() -> tuple[int, int, int, int, int, int] | None:
    """(allocations, deallocations, freelist_hits, slabs_allocated, bytes_from_slabs,
    large_allocations), or None in pure-Python mode."""
    if not cython.compiled:
        return None
    stats: typing.Any = pool().stats()
    return (
        stats.allocations,
        stats.deallocations,
        stats.freelist_hits,
        stats.slabs_allocated,
        stats.bytes_from_slabs,
        stats.large_allocations,
    )


if cython.compiled:

    @cython.final
    @cython.cclass
    class Bitmask:
        """Python-visible wrapper around `BitmaskData`, a plain C++ value.

        Used for long-lived, rarely-copied bitmasks (`ResourceCollection.resource_bitmask`).
        `GraphRequirementList` embeds `BitmaskData` directly instead, to stay GC-free; reach its
        raw value through `.data` when comparing against one of those (see graph_requirement.py).
        """

        if typing.TYPE_CHECKING:
            # Declared in bitmask.pxd; repeated here just so mypy knows it exists.
            data: BitmaskData

        # `data` default-constructs empty; always built via create()/create_native()

        @classmethod
        def create(cls) -> Bitmask:
            return Bitmask.__new__(Bitmask)

        @staticmethod
        @cython.cfunc
        def create_native() -> Bitmask:
            return Bitmask.__new__(Bitmask)

        def __eq__(self, other: object) -> cython.bint:
            return isinstance(other, Bitmask) and self.equals_to(other)

        @cython.ccall
        def equals_to(self, other: Bitmask) -> cython.bint:
            return self.data.equals_to(other.data)

        def __hash__(self) -> cython.int:
            return hash(self.data.hash_value())

        @cython.ccall
        def hash_value(self) -> cython.ulonglong:
            return self.data.hash_value()

        @cython.ccall
        def set_bit(self, index: cython.longlong) -> cython.void:
            self.data.set_bit(index)

        @cython.ccall
        def unset_bit(self, index: cython.longlong) -> cython.void:
            self.data.unset_bit(index)

        @cython.ccall
        @cython.inline
        def is_set(self, index: cython.longlong) -> cython.bint:
            return self.data.is_set(index)

        @cython.ccall
        def union(self, other: Bitmask) -> cython.void:
            """For every bit set in other, also set in self"""
            self.data.union(other.data)

        @cython.ccall
        def share_at_least_one_bit(self, other: Bitmask) -> cython.bint:
            return self.data.share_at_least_one_bit(other.data)

        @cython.ccall
        # @cython.exceptval(check=False)
        def is_subset_of(self, other: Bitmask) -> cython.bint:
            return self.data.is_subset_of(other.data)

        @cython.ccall
        def get_set_bits(self) -> vector[cython.size_t]:
            """Gets a list of all set bit indices."""
            # mypy's BitmaskData stand-in returns list[int], not a std::vector.
            return self.data.get_set_bits()  # type: ignore[return-value]

        @cython.ccall
        def num_set_bits(self) -> cython.int:
            return self.data.num_set_bits()

        @cython.ccall
        def is_empty(self) -> cython.bint:
            return self.data.is_empty()

        @cython.ccall
        def copy(self) -> Bitmask:
            result: Bitmask = Bitmask.__new__(Bitmask)
            result.data = self.data.copy()
            return result
else:

    class BitmaskInt:
        __slots__ = ("_mask",)
        _mask: int

        def __init__(self, mask: int):
            self._mask = mask

        @classmethod
        def create(cls) -> typing.Self:
            return cls(0)

        @staticmethod
        def create_native() -> BitmaskInt:
            return BitmaskInt(0)

        def __eq__(self, other: object) -> cython.bint:
            return isinstance(other, BitmaskInt) and self.equals_to(other)

        def equals_to(self, other: BitmaskInt) -> cython.bint:
            return self._mask == other._mask

        def __hash__(self) -> cython.int:
            return hash(self._mask)

        def hash_value(self) -> int:
            return self._mask

        @property
        def data(self) -> typing.Self:
            # Compiled mode stores masks in a separate BitmaskData value, reached via `.data`;
            # pure mode's BitmaskInt already is that value, so `.data` is just itself.
            return self

        def set_bit(self, index: int) -> None:
            self._mask |= 1 << index

        def unset_bit(self, index: int) -> None:
            mask = 1 << index
            if self._mask & mask:
                self._mask -= mask

        def is_set(self, index: int) -> bool:
            return self._mask & (1 << index) != 0

        def union(self, other: BitmaskInt) -> None:
            """For every bit set in other, also set in self"""
            self._mask |= other._mask

        def share_at_least_one_bit(self, other: BitmaskInt) -> bool:
            return self._mask & other._mask != 0

        def is_subset_of(self, other: BitmaskInt) -> cython.bint:
            return self._mask & other._mask == self._mask

        def get_set_bits(self) -> list[int]:
            """Gets a list of all set bit indices."""
            result: list[int] = []

            mask_str = bin(self._mask)[2:]
            idx = len(mask_str)
            bit_inverse = idx - 1
            while idx != -1:
                idx = mask_str.rfind("1", 0, idx)
                if idx != -1:
                    result.append(bit_inverse - idx)

            return result

        def num_set_bits(self) -> cython.int:
            return self._mask.bit_count()

        def is_empty(self) -> cython.bint:
            return self._mask == 0

        def copy(self) -> typing.Self:
            return self.__class__(self._mask)

    Bitmask = BitmaskInt  # type: ignore[assignment, misc]
    BitmaskData = BitmaskInt
    PyObject = object
