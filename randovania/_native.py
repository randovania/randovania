# distutils: language=c++

from __future__ import annotations

import copy
import typing

if typing.TYPE_CHECKING:
    # The package is named `Cython`, so in a case-sensitive system mypy fails to find cython with just `import cython`
    import Cython as cython
else:
    # However cython's compiler seems to expect the import o be this way, otherwise `cython.compiled` breaks
    import cython

if typing.TYPE_CHECKING:
    from randovania.game_description.game_database_view import ResourceDatabaseView
    from randovania.game_description.resources.resource_info import ResourceGain, ResourceGainTuple, ResourceInfo

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


@cython.cclass
class ResourceCollection:
    resource_bitmask = cython.declare(Bitmask, visibility="public")
    _resource_array = cython.declare(vector[cython.int])
    _existing_resources: dict[int, ResourceInfo] = cython.declare(dict[int, object])  # type: ignore[arg-type]
    _damage_reduction_cache = cython.declare(dict[int, float] | None)  # type: ignore[call-overload]
    _resource_database: ResourceDatabaseView = cython.declare(object)  # type: ignore[assignment]

    def __init__(self, resource_database: ResourceDatabaseView, resource_array: vector[cython.int]) -> None:
        self.resource_bitmask = Bitmask.create()
        self._resource_array = resource_array
        self._existing_resources = {}
        self._damage_reduction_cache = None
        self._resource_database = resource_database

    @classmethod
    def with_resource_count(cls, resource_database: ResourceDatabaseView, count: cython.size_t) -> ResourceCollection:
        result = cls(resource_database, vector[cython.int]())
        if cython.compiled:
            result._resize_array_to_fit(count)
        else:
            result._resource_array._data = [0] * count
        return result

    @cython.ccall
    def _resize_array_to_fit(self, size: cython.size_t) -> None:
        target_size: cython.size_t = self._resource_array.size()
        if target_size < 10:
            target_size = 10
        while target_size < size:
            target_size *= 2
        self._resource_array.resize(target_size, 0)

    def __getitem__(self, item: ResourceInfo) -> int:
        return self.get(item)

    def current_array_size(self) -> cython.size_t:
        return self._resource_array.size()

    @cython.ccall
    def get(self, item: ResourceInfo) -> cython.int:
        resource_index: cython.int = item.resource_index
        if resource_index < self._resource_array.size():
            return self._resource_array[resource_index]
        else:
            return 0

    def __str__(self) -> str:
        return f"<ResourceCollection with {self.num_resources} resources>"

    @property
    def _comparison_tuple(self) -> ResourceGainTuple:
        return tuple(self.as_resource_gain())

    def __hash__(self) -> int:
        return hash(self._comparison_tuple)

    def __eq__(self, other: object) -> cython.bint:
        return isinstance(other, ResourceCollection) and (self._comparison_tuple == other._comparison_tuple)

    @property
    def num_resources(self) -> int:
        return len(self._existing_resources)

    @cython.ccall
    def has_resource(self, resource: ResourceInfo) -> cython.bint:
        return self.get(resource) > 0

    def is_resource_set(self, resource: ResourceInfo) -> cython.bint:
        """
        Checks if the given resource has a value explicitly set, instead of using the fallback of 0.
        :param resource:
        :return:
        """
        return resource.resource_index in self._existing_resources

    def set_resource(self, resource: ResourceInfo, quantity: cython.int) -> None:
        """Sets the quantity of the given resource to be exactly the given value.
        This method should be used in exceptional cases only. For common usage, use `add_resource_gain`.
        """
        quantity = max(quantity, 0)
        resource_index: cython.int = resource.resource_index
        self._damage_reduction_cache = None
        if self._resource_array.size() <= resource_index:
            self._resize_array_to_fit(resource_index + 1)
        self._resource_array[resource_index] = quantity
        self._existing_resources[resource_index] = resource

        if quantity > 0:
            self.resource_bitmask.set_bit(resource_index)
        else:
            self.resource_bitmask.unset_bit(resource_index)

    @classmethod
    def from_dict(cls, view: ResourceDatabaseView, resources: dict[ResourceInfo, int]) -> ResourceCollection:
        result = view.create_resource_collection()
        result.add_resource_gain(resources.items())
        return result

    @classmethod
    def from_resource_gain(cls, game: ResourceDatabaseView, resource_gain: ResourceGain) -> ResourceCollection:
        result = game.create_resource_collection()
        result.add_resource_gain(resource_gain)
        return result

    @cython.locals(resource=object, quantity=cython.int)
    def add_resource_gain(self, resource_gain: ResourceGain) -> None:
        self._damage_reduction_cache = None
        for resource, quantity in resource_gain:
            resource_index: cython.size_t = resource.resource_index
            if self._resource_array.size() <= resource_index:
                self._resize_array_to_fit(resource_index + 1)

            new_amount: cython.int = self._resource_array[resource_index] + quantity
            if new_amount < 0:
                new_amount = 0
            self._resource_array[resource_index] = new_amount
            self._existing_resources[resource_index] = resource

            if new_amount > 0:
                self.resource_bitmask.set_bit(resource_index)
            else:
                self.resource_bitmask.unset_bit(resource_index)

    def as_resource_gain(self) -> ResourceGain:
        for index, resource in self._existing_resources.items():
            yield resource, self._resource_array[index]

    def remove_resource(self, resource: ResourceInfo) -> None:
        """
        Removes the given resource, making `is_resource_set` return False for it.
        This should be used in exceptional cases only. Consider `add_resource_gain` with negative gain instead.
        """
        resource_index: cython.int = resource.resource_index
        self._existing_resources.pop(resource_index, None)

        if resource_index < self._resource_array.size():
            self._resource_array[resource_index] = 0

        self.resource_bitmask.unset_bit(resource_index)

    def duplicate(self) -> ResourceCollection:
        result: ResourceCollection = ResourceCollection(self._resource_database, copy.copy(self._resource_array))
        result._existing_resources.update(self._existing_resources)
        result.resource_bitmask = self.resource_bitmask.copy()
        return result

    @cython.ccall
    # @cython.exceptval(check=False)
    def get_damage_reduction(self, resource: ResourceInfo) -> cython.float:
        if self._damage_reduction_cache is None:
            self._damage_reduction_cache = {}

        reduction: float | None = self._damage_reduction_cache.get(resource.resource_index)

        if reduction is None:
            reduction = self._resource_database.get_damage_reduction(resource, self)
            self._damage_reduction_cache[resource.resource_index] = reduction

        return reduction

    def __copy__(self) -> ResourceCollection:
        return self.duplicate()
