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

# ruff: noqa: UP046

if cython.compiled:
    if not typing.TYPE_CHECKING:
        from cython.cimports.libcpp.bit import popcount
        from cython.cimports.libcpp.vector import vector
else:
    from randovania.lib.cython_helper import Vector as vector
    from randovania.lib.cython_helper import popcount

if cython.compiled:

    @cython.final
    @cython.cclass
    class Bitmask:
        def __init__(self, masks: vector[cython.ulonglong]):
            self._masks = masks

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
            if self._masks.size() != other._masks.size():
                return False

            for idx in range(self._masks.size()):
                if self._masks[idx] != other._masks[idx]:
                    return False

            return True

        def __hash__(self) -> cython.int:
            result: cython.ulonglong = 0
            for idx in range(self._masks.size()):
                result ^= self._masks[idx]
            return hash(result)

        @cython.ccall
        def set_bit(self, index: cython.longlong) -> cython.void:
            one: cython.ulonglong = 1

            arr_idx: cython.size_t = index >> 6
            bit_idx: cython.ulonglong = index & 63
            if arr_idx >= self._masks.size():
                for _ in range(arr_idx - self._masks.size() + 1):
                    self._masks.push_back(0)

            self._masks[arr_idx] |= one << bit_idx

        @cython.ccall
        def unset_bit(self, index: cython.longlong) -> cython.void:
            one: cython.ulonglong = 1

            arr_idx: cython.size_t = index >> 6
            if arr_idx < self._masks.size():
                bit_idx: cython.ulonglong = index & 63
                mask: cython.ulonglong = one << bit_idx
                if self._masks[arr_idx] & mask:
                    self._masks[arr_idx] -= mask

                    while not self._masks.empty() and self._masks.back() == 0:
                        self._masks.pop_back()

        @cython.ccall
        @cython.inline
        def is_set(self, index: cython.longlong) -> cython.bint:
            one: cython.ulonglong = 1

            arr_idx: cython.size_t = index >> 6
            if arr_idx < self._masks.size():
                bit_idx: cython.ulonglong = index & 63
                mask: cython.ulonglong = one << bit_idx
                return self._masks[arr_idx] & mask != 0
            else:
                return False

        @cython.ccall
        def union(self, other: Bitmask) -> cython.void:
            """For every bit set in other, also set in self"""
            idx: cython.size_t
            last_shared: cython.size_t = min(self._masks.size(), other._masks.size())

            if other._masks.size() > self._masks.size():
                for idx in range(self._masks.size(), other._masks.size()):
                    self._masks.push_back(other._masks[idx])

            for idx in range(last_shared):
                self._masks[idx] |= other._masks[idx]

        @cython.locals(idx=cython.size_t)
        @cython.ccall
        def share_at_least_one_bit(self, other: Bitmask) -> cython.bint:
            last_shared: cython.size_t = min(self._masks.size(), other._masks.size())
            for idx in range(last_shared):
                if self._masks[idx] & other._masks[idx]:
                    return True

            return False

        @cython.locals(idx=cython.size_t, self_mask=cython.ulonglong, other_mask=cython.ulonglong)
        @cython.ccall
        # @cython.exceptval(check=False)
        def is_subset_of(self, other: Bitmask) -> cython.bint:
            if self._masks.size() > other._masks.size():
                return False

            for idx in range(self._masks.size()):
                self_mask = self._masks[idx]
                other_mask = other._masks[idx]
                if self_mask & other_mask != self_mask:
                    return False

            return True

        @cython.ccall
        def get_set_bits(self) -> vector[cython.size_t]:
            """Gets a list of all set bit indices."""
            result: vector[cython.size_t] = vector[cython.size_t]()
            # For non-Cython callers, this results in a regular list

            idx: cython.size_t
            for idx in range(self._masks.size()):
                mask: cython.ulonglong = self._masks[idx]
                if mask != 0:
                    # For each 64-bit chunk, find all set bits
                    base_bit_index: cython.longlong = idx * 64
                    bit_pos: cython.int = 0
                    temp_mask: cython.ulonglong = mask

                    while temp_mask != 0:
                        if temp_mask & 1:
                            result.push_back(base_bit_index + bit_pos)
                        temp_mask >>= 1
                        bit_pos += 1

            return result

        @cython.ccall
        def num_set_bits(self) -> cython.int:
            result: cython.int = 0

            # Use compiler built-in for popcount
            for idx in range(self._masks.size()):
                mask: cython.ulonglong = self._masks[idx]
                result += popcount(mask)

            return result

        @cython.ccall
        def is_empty(self) -> cython.bint:
            return self._masks.empty()

        @cython.ccall
        def copy(self) -> Bitmask:
            result: Bitmask = Bitmask.__new__(Bitmask)
            result._masks = self._masks
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
            return bin(self._mask).count("1")

        def is_empty(self) -> cython.bint:
            return self._mask == 0

        def copy(self) -> typing.Self:
            return self.__class__(self._mask)

    Bitmask = BitmaskInt  # type: ignore[assignment, misc]
    PyObject = object
