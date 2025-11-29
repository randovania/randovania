# distutils: language=c++

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    # The package is named `Cython`, so in a case-sensitive system mypy fails to find cython with just `import cython`
    import Cython as cython
else:
    # However cython's compiler seems to expect the import o be this way, otherwise `cython.compiled` breaks
    import cython

# ruff: noqa: UP046

if typing.TYPE_CHECKING:
    from randovania._native_helper import Vector as vector
    from randovania._native_helper import popcount

elif cython.compiled:
    from cython.cimports.libcpp.bit import popcount
    from cython.cimports.libcpp.vector import vector
else:
    from randovania._native_helper import Vector as vector

if cython.compiled:

    @cython.cclass
    class Bitmask:
        _masks = cython.declare(vector[cython.ulonglong], visibility="public")

        def __init__(self, masks: vector[cython.ulonglong]):
            assert cython.compiled
            self._masks = masks

        @classmethod
        def create(cls) -> typing.Self:
            return cls(vector[cython.ulonglong]())

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
        def set_bit(self, index: cython.longlong) -> None:
            one: cython.ulonglong = 1

            arr_idx: cython.size_t = index >> 6
            bit_idx: cython.ulonglong = index & 63
            if arr_idx >= self._masks.size():
                for _ in range(arr_idx - self._masks.size() + 1):
                    self._masks.push_back(0)

            self._masks[arr_idx] |= one << bit_idx

        @cython.ccall
        def unset_bit(self, index: cython.longlong) -> None:
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
        def is_set(self, index: cython.longlong) -> cython.bint:
            one: cython.ulonglong = 1

            arr_idx: cython.size_t = index >> 6
            if arr_idx < self._masks.size():
                bit_idx: cython.ulonglong = index & 63
                mask: cython.ulonglong = one << bit_idx
                return self._masks[arr_idx] & mask != 0
            else:
                return False

        @cython.locals(idx=cython.size_t)
        @cython.ccall
        def union(self, other: Bitmask) -> None:
            """For every bit set in other, also set in self"""
            last_shared: cython.size_t = min(self._masks.size(), other._masks.size())

            if other._masks.size() > self._masks.size():
                for idx in range(self._masks.size(), other._masks.size()):
                    self._masks.push_back(other._masks[idx])

            for idx in range(last_shared):
                self._masks[idx] |= other._masks[idx]

        @cython.locals(idx=cython.size_t)
        def share_at_least_one_bit(self, other: Bitmask) -> cython.bint:
            last_shared: cython.size_t = min(self._masks.size(), other._masks.size())
            for idx in range(last_shared):
                if self._masks[idx] & other._masks[idx]:
                    return True

            return False

        @cython.locals(idx=cython.size_t)
        @cython.ccall
        # @cython.exceptval(check=False)
        def is_subset_of(self, other: Bitmask) -> cython.bint:
            if self._masks.size() > other._masks.size():
                return False

            for idx in range(self._masks.size()):
                if self._masks[idx] & other._masks[idx] != self._masks[idx]:
                    return False

            return True

        @cython.ccall
        def get_set_bits(self) -> list[int]:
            """Gets a list of all set bit indices."""
            result: list[int] = []

            for idx in range(self._masks.size()):
                mask: cython.ulonglong = self._masks[idx]
                if mask != 0:
                    # For each 64-bit chunk, find all set bits
                    base_bit_index: cython.longlong = idx * 64
                    bit_pos: cython.int = 0
                    temp_mask: cython.ulonglong = mask

                    while temp_mask != 0:
                        if temp_mask & 1:
                            result.append(base_bit_index + bit_pos)
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

        def copy(self) -> typing.Self:
            return self.__class__(self._masks)

else:

    class BitmaskInt:
        __slots__ = ("_mask",)
        _mask: int

        def __init__(self, mask: int):
            self._mask = mask

        @classmethod
        def create(cls) -> typing.Self:
            return cls(0)

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
            if self._mask != 0:
                bit_pos = 0
                temp_mask = self._mask
                while temp_mask != 0:
                    if temp_mask & 1:
                        result.append(bit_pos)
                    temp_mask >>= 1
                    bit_pos += 1
            return result

        def num_set_bits(self) -> cython.int:
            return bin(self._mask).count("1")

        @cython.ccall
        def is_empty(self) -> cython.bint:
            return self._mask == 0

        def copy(self) -> typing.Self:
            return self.__class__(self._mask)

    Bitmask = BitmaskInt  # type: ignore[assignment, misc]
