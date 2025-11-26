# distutils: language=c++

from __future__ import annotations

import copy
import functools
import itertools
import logging
import typing

if typing.TYPE_CHECKING:
    # The package is named `Cython`, so in a case-sensitive system mypy fails to find cython with just `import cython`
    import Cython as cython
else:
    # However cython's compiler seems to expect the import o be this way, otherwise `cython.compiled` breaks
    import cython

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

    from randovania.game_description.game_database_view import ResourceDatabaseView
    from randovania.game_description.resources.resource_info import ResourceGain, ResourceGainTuple, ResourceInfo
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraphNode
    from randovania.resolver.damage_state import DamageState
    from randovania.resolver.logic import Logic

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


@cython.ccall
def _is_later_progression_item(
    resource: ResourceInfo, progressive_chain_info: None | tuple[Sequence[ResourceInfo], int]
) -> bool:
    if not progressive_chain_info:
        return False
    progressive_chain, index = progressive_chain_info
    return resource in progressive_chain and progressive_chain.index(resource) > index


@cython.ccall
def _downgrade_progressive_item(
    item_resource: ResourceInfo, progressive_chain_info: tuple[Sequence[ResourceInfo], int]
) -> ResourceInfo:
    progressive_chain, _ = progressive_chain_info
    return progressive_chain[progressive_chain.index(item_resource) - 1]


@cython.cclass
class GraphRequirementList:
    """
    Represents a list of resource requirements that must all be satisfied at once (`AND`).
    These requirements are split into 4 groups:
    - A resource must be >= 1.
    - A resource must be 0.
    - A resource must be >= N.
    - A damage resource and how much.
    The first two are implemented with bitmasks.
    """

    _set_bitmask: Bitmask
    _negate_bitmask: Bitmask
    _other_resources: dict[ResourceInfo, cython.int]
    _damage_resources: dict[ResourceInfo, cython.int]

    _set_resources: list[ResourceInfo]
    _negate_resources: list[ResourceInfo]

    _frozen: cython.bint

    def __init__(self) -> None:
        self._set_bitmask = Bitmask.create()
        self._negate_bitmask = Bitmask.create()
        self._other_resources: dict[ResourceInfo, cython.int] = {}
        self._damage_resources: dict[ResourceInfo, cython.int] = {}

        self._set_resources = []
        self._negate_resources = []

        self._frozen = False

    def __eq__(self, other: object) -> cython.bint:
        if isinstance(other, GraphRequirementList):
            return self.equals_to(other)
        return False

    @cython.ccall
    # @cython.exceptval(check=False)
    def equals_to(self, other: GraphRequirementList) -> cython.bint:
        return (
            self._set_bitmask.equals_to(other._set_bitmask)
            and self._negate_bitmask.equals_to(other._negate_bitmask)
            and self._other_resources == other._other_resources
            and self._damage_resources == other._damage_resources
        )

    def __hash__(self) -> int:
        # TODO: hashable objects are supposed to be immutable, but this will need a bit of testing
        # if not self._frozen:
        #     raise RuntimeError("Cannot hash a non-frozen GraphRequirementList")

        return hash(
            (
                self._set_bitmask,
                self._negate_bitmask,
                tuple(self._other_resources.items()),
                tuple(self._damage_resources.items()),
            )
        )

    def is_frozen(self) -> cython.bint:
        """Returns True if `freeze` was previously called."""
        return self._frozen

    def freeze(self) -> None:
        """Prevents any further modifications to this GraphRequirementList. Copies won't be frozen."""
        self._frozen = True

    def _check_can_write(self) -> None:
        if self._frozen:
            raise RuntimeError("Cannot modify a frozen GraphRequirementList")

    def complexity_key_for_simplify(self: GraphRequirementList) -> tuple[int, int, int]:
        """
        A value that indicates how "complex" this requirement is. Used for sorting the alternatives in
        GraphRequirementSet.optimize_alternatives
        """
        return (
            self._set_bitmask.num_set_bits() + self._negate_bitmask.num_set_bits(),
            len(self._other_resources),
            len(self._damage_resources),
        )

    def __copy__(self) -> GraphRequirementList:
        result = GraphRequirementList()
        result._set_bitmask = self._set_bitmask.copy()
        result._negate_bitmask = self._negate_bitmask.copy()
        result._other_resources = copy.copy(self._other_resources)
        result._damage_resources = copy.copy(self._damage_resources)
        result._set_resources = copy.copy(self._set_resources)
        result._negate_resources = copy.copy(self._negate_resources)
        return result

    def __str__(self) -> str:
        parts = sorted(
            f"{resource.resource_type.non_negated_prefix}{resource}"
            for resource in self._set_resources
            if resource not in self._other_resources
        )
        parts.extend(
            sorted(f"{resource.resource_type.negated_prefix}{resource}" for resource in self._negate_resources)
        )
        parts.extend(sorted(f"{resource} ≥ {amount}" for resource, amount in self._other_resources.items()))
        parts.extend(sorted(f"{resource} ≥ {amount}" for resource, amount in self._damage_resources.items()))
        if parts:
            return " and ".join(parts)
        else:
            return "Trivial"

    @cython.ccall
    def num_requirements(self) -> cython.int:
        """Returns the total number of resource requirements in this list."""
        return self._set_bitmask.num_set_bits() + self._negate_bitmask.num_set_bits() + len(self._damage_resources)

    @cython.ccall
    def all_resources(self, *, include_damage: cython.bint = True) -> set[ResourceInfo]:
        """Returns a set of all resources involved in this requirement."""
        result = set(self._set_resources)
        result.update(self._negate_resources)
        if include_damage:
            result.update(self._damage_resources)
        return result

    @cython.ccall
    def get_requirement_for(
        self, resource: ResourceInfo, include_damage: cython.bint = True
    ) -> tuple[cython.int, cython.bint]:
        """
        Gets the amount and negate status for the given resource. Damage resources are ignored.
        :param resource:
        :return: A tuple, containing the amount and if it's a negate requirement.
        """
        if resource in self._other_resources:
            return self._other_resources[resource], False

        resource_index: cython.int = resource.resource_index

        if self._set_bitmask.is_set(resource_index):
            return 1, False

        if self._negate_bitmask.is_set(resource_index):
            return 1, True

        if include_damage and resource in self._damage_resources:
            return self._damage_resources[resource], False

        return 0, False

    @cython.locals(amount=cython.int, other=object, resource_index=cython.int, health=cython.float)
    @cython.ccall
    # @cython.exceptval(check=False)
    def satisfied(self, resources: ResourceCollection, health: cython.float) -> cython.bint:
        """Checks if the given resources and health satisfies this requirement."""
        if not self._set_bitmask.is_subset_of(resources.resource_bitmask):
            return False

        if not self._negate_bitmask.is_empty():
            if self._negate_bitmask.is_subset_of(resources.resource_bitmask):
                return False

        for other in self._other_resources:
            amount = self._other_resources[other]
            if resources.get(other) < amount:
                return False

        for other in self._damage_resources:
            damage: cython.int = self._damage_resources[other]
            health -= damage * resources.get_damage_reduction(other)
            if health <= 0:
                return False

        return True

    @cython.locals(other=object)
    @cython.ccall
    # @cython.exceptval(check=False)
    def damage(self, resources: ResourceCollection) -> cython.float:
        """
        How much damage this requirement causes with the reductions of the given resources.
        This ignores all other requirements.
        """
        result: cython.float = 0
        damage: cython.int

        for other in self._damage_resources:
            damage = self._damage_resources[other]
            result += damage * resources.get_damage_reduction(other)

        return result

    @cython.ccall
    def and_with(self, merge: GraphRequirementList) -> bool:
        """
        Modifies this requirement to also check for all the requirements in `merge`.
        Returns False if the combination is impossible to satisfy (mix of set and negate requirements).
        """

        self._check_can_write()

        # Check if there's any conflict between set and negate requirements
        if merge._set_bitmask.share_at_least_one_bit(self._negate_bitmask):
            return False

        if self._set_bitmask.share_at_least_one_bit(merge._negate_bitmask):
            return False

        for resource in merge._set_resources:
            if not self._set_bitmask.is_set(resource.resource_index):
                self._set_resources.append(resource)
        self._set_bitmask.union(merge._set_bitmask)

        for resource in merge._negate_resources:
            if not self._negate_bitmask.is_set(resource.resource_index):
                self._negate_resources.append(resource)
        self._negate_bitmask.union(merge._negate_bitmask)

        amount: cython.int
        for other, amount in merge._other_resources.items():
            self._other_resources[other] = max(self._other_resources.get(other, 0), amount)

        damage: cython.int
        for other, damage in merge._damage_resources.items():
            self._damage_resources[other] = self._damage_resources.get(other, 0) + damage

        return True

    @cython.ccall
    def copy_then_and_with(self, right: GraphRequirementList) -> GraphRequirementList | None:
        """
        Copies this requirement and then performs `and_with`, but more efficiently.
        Returns None if the combination is impossible to satisfy (mix of set and negate requirements).
        """
        result = GraphRequirementList()

        # Copy and union bitmasks
        result._set_bitmask = self._set_bitmask.copy()
        result._set_bitmask.union(right._set_bitmask)
        result._negate_bitmask = self._negate_bitmask.copy()
        result._negate_bitmask.union(right._negate_bitmask)

        # Check if there's any conflict between set and negate requirements
        if result._set_bitmask.share_at_least_one_bit(result._negate_bitmask):
            return None

        # Union _set_resources and _negate_resources (avoiding duplicates using bitmask)
        result._set_resources = list(self._set_resources)
        for resource in right._set_resources:
            if not self._set_bitmask.is_set(resource.resource_index):
                result._set_resources.append(resource)

        result._negate_resources = list(self._negate_resources)
        for resource in right._negate_resources:
            if not self._negate_bitmask.is_set(resource.resource_index):
                result._negate_resources.append(resource)

        # Merge _other_resources with max values
        result._other_resources = dict(self._other_resources)
        for resource, amount in right._other_resources.items():
            result._other_resources[resource] = max(result._other_resources.get(resource, 0), amount)

        # Merge _damage_resources with sum
        result._damage_resources = dict(self._damage_resources)
        for resource, damage in right._damage_resources.items():
            result._damage_resources[resource] = result._damage_resources.get(resource, 0) + damage

        return result

    @cython.ccall
    def copy_then_remove_entries_for_set_resources(self, resources: ResourceCollection) -> GraphRequirementList | None:
        from randovania.game_description.resources.item_resource_info import ItemResourceInfo

        result = GraphRequirementList()

        for resource in self.all_resources(include_damage=False):
            amount, negate = self.get_requirement_for(resource)
            if resources.is_resource_set(resource):
                if negate:
                    satisfied = resources.get(resource) < amount
                else:
                    satisfied = resources.get(resource) >= amount

                if satisfied:
                    continue
                elif not isinstance(resource, ItemResourceInfo) or resource.max_capacity <= 1:
                    # TODO: some implementation that doesn't need imports?
                    return None
            result.add_resource(resource, amount, negate)

        for resource in self._damage_resources:
            result.add_resource(resource, self._damage_resources[resource], False)

        return result

    @cython.ccall
    def add_resource(self, resource: ResourceInfo, amount: cython.int, negate: cython.bint) -> None:
        """
        Adds a new resource requirement to this.
        If negate is set, amount must be 1.
        """
        self._check_can_write()

        if amount == 0:
            return

        assert not negate or amount == 1

        if resource.resource_type.is_damage():
            self._damage_resources[resource] = self._damage_resources.get(resource, 0) + amount
            return

        resource_index: cython.int = resource.resource_index

        if negate:
            target_list = self._negate_resources
            target_bitmask = self._negate_bitmask
            other_bitmask = self._set_bitmask
        else:
            target_list = self._set_resources
            target_bitmask = self._set_bitmask
            other_bitmask = self._negate_bitmask

        if other_bitmask.is_set(resource_index):
            raise ValueError("Cannot add resource requirement that conflicts with existing requirements")

        if not target_bitmask.is_set(resource_index):
            target_list.append(resource)

        target_bitmask.set_bit(resource_index)
        if amount > 1:
            self._other_resources[resource] = max(self._other_resources.get(resource, 0), amount)

    @cython.ccall
    def isolate_damage_requirements(self, resources: ResourceCollection) -> GraphRequirementList | None:
        """
        Returns a new GraphRequirement with only the damage components.
        :param resources:
        :return: None, if it's currently not satisfied.
        """
        if not self._set_bitmask.is_empty():
            # A satisfied resource requirement becomes Trivial, which is then discarded
            # An unsatisfied resource requirement becomes Impossible, which means the entire And is impossible
            if not self._set_bitmask.is_subset_of(resources.resource_bitmask):
                return None

        if not self._negate_bitmask.is_empty():
            if self._negate_bitmask.share_at_least_one_bit(resources.resource_bitmask):
                return None

        for other, amount in self._other_resources.items():
            if resources.get(other) < amount:
                return None

        result = GraphRequirementList()

        for other, amount in self._damage_resources.items():
            if resources.get_damage_reduction(other) == 0:
                return GraphRequirementList()

            result._damage_resources[other] = amount

        return result

    @cython.ccall
    def is_requirement_superset(self, subset_req: GraphRequirementList) -> cython.bint:
        """Check if self is a strict superset of subset_req.

        Returns True if self contains all requirements of subset_req and is more restrictive.
        This means self requires everything subset_req requires, plus potentially more.
        """
        # Check bitmasks - superset must contain all bits from subset
        if not subset_req._set_bitmask.is_subset_of(self._set_bitmask):
            return False

        if not subset_req._negate_bitmask.is_subset_of(self._negate_bitmask):
            return False

        # Check _other_resources - superset must have >= amounts for all resources in subset
        for resource, amount in subset_req._other_resources.items():
            if self._other_resources.get(resource, 0) < amount:
                return False

        # Check _damage_resources - superset must have >= amounts for all damage in subset
        for resource, damage in subset_req._damage_resources.items():
            if self._damage_resources.get(resource, 0) < damage:
                return False

        # Remove duplicates
        return True

    @cython.ccall
    def simplify_requirement_list(
        self,
        resources: ResourceCollection,
        health_for_damage_requirements: cython.float,
        node_resources: Sequence[ResourceInfo],
        progressive_item_info: None | tuple[Sequence[ResourceInfo], int],
    ) -> GraphRequirementList | None:
        """Used by resolver.py for `_simplify_additional_requirement_set`"""

        result = GraphRequirementList()
        something_set: cython.bint = False

        for resource in itertools.chain(self._set_resources, self._negate_resources):
            amount, negate = self.get_requirement_for(resource)

            if negate:
                if resources.get(resource) == 0:
                    continue
                if resource in node_resources:
                    return None
            else:
                if resources.get(resource) >= amount:
                    continue

            if _is_later_progression_item(resource, progressive_item_info):
                assert progressive_item_info is not None
                result.add_resource(
                    _downgrade_progressive_item(resource, progressive_item_info),
                    1,
                    False,
                )
                something_set = True

            else:
                something_set = True
                result.add_resource(resource, amount, negate)

        if self.damage(resources) >= health_for_damage_requirements:
            something_set = True
            result._damage_resources = copy.copy(self._damage_resources)

        if not something_set:
            return None

        return result

    @cython.ccall
    def _single_resource_optimize_logic(self, single_req_mask: Bitmask) -> cython.int:
        """
        Specialized logic for GraphRequirementSet.optimize_alternatives.

        :param single_req_mask: A bitmask used internally to keep track of single-requirement alternatives.
        :return:
            0 if this requirement shares a requirement with a single-requirement alternative
            1 if this is a single-requirement alternative
            2 if nothing was decided, calculate is_superset normally.
        """
        if self._set_bitmask.share_at_least_one_bit(single_req_mask):
            # We already have a requirement that is just one of these resources
            return 0

        if self.num_requirements() == 1 and not self._set_bitmask.is_empty():
            single_req_mask.union(self._set_bitmask)
            return 1
        else:
            return 2


@cython.cclass
class GraphRequirementSet:
    """
    Contains a list of GraphRequirement, but only one needs to be satisfied (OR).

    These two classes together represents a `Requirement` in disjunctive normal form.
    """

    _alternatives: list[GraphRequirementList] = cython.declare(list[GraphRequirementList])
    _frozen: cython.bint

    def __init__(self) -> None:
        self._alternatives = []
        self._frozen = False

    def __copy__(self) -> GraphRequirementSet:
        result = GraphRequirementSet()
        for it in self._alternatives:
            result._alternatives.append(copy.copy(it))
        return result

    __hash__ = None  # type: ignore[assignment]

    def __eq__(self, other: object) -> cython.bint:
        if isinstance(other, GraphRequirementSet):
            return self.equals_to(other)
        return False

    @cython.ccall
    # @cython.exceptval(check=False)
    def equals_to(self, other: GraphRequirementSet) -> cython.bint:
        return self._alternatives == other._alternatives

    def is_frozen(self) -> cython.bint:
        """Returns True if `freeze` was previously called."""
        return self._frozen

    def freeze(self) -> None:
        """Prevents any further modifications to this GraphRequirementSet and any nested GraphRequirementList."""
        self._frozen = True
        for it in self._alternatives:
            it.freeze()

    def _check_can_write(self) -> None:
        if self._frozen:
            raise RuntimeError("Cannot modify a frozen GraphRequirementSet")

    @property
    def alternatives(self) -> tuple[GraphRequirementList, ...]:
        return tuple(self._alternatives)

    def add_alternative(self, alternative: GraphRequirementList) -> None:
        self._check_can_write()
        self._alternatives.append(alternative)

    def extend_alternatives(self, alternatives: Iterable[GraphRequirementList]) -> None:
        self._check_can_write()
        self._alternatives.extend(alternatives)

    @cython.locals(idx=cython.int, alt=GraphRequirementList)
    @cython.ccall
    # @cython.exceptval(check=False)
    def satisfied(self, resources: ResourceCollection, energy: cython.float) -> cython.bint:
        """Checks if the given resources and health satisfies at least one alternative."""
        alternatives: list[GraphRequirementList] = self._alternatives

        for idx in range(len(alternatives)):
            alt: GraphRequirementList = alternatives[idx]
            if alt.satisfied(resources, energy):
                return True

        return False

    @cython.locals(idx=cython.int, alt=GraphRequirementList, new_dmg=cython.float, damage=cython.float)
    @cython.ccall
    # @cython.exceptval(check=False)
    def damage(self, resources: ResourceCollection) -> cython.float:
        """
        The least amount of damage from any alternative.
        """
        damage = float("inf")

        for idx in range(len(self._alternatives)):
            alt = self._alternatives[idx]
            new_dmg = alt.damage(resources)
            if new_dmg <= 0.0:
                return new_dmg
            if new_dmg < damage:
                damage = new_dmg

        return damage

    @cython.ccall
    def all_alternative_and_with(self, merge: GraphRequirementList) -> None:
        """
        Calls `and_with` for every alternative.
        If `and_with` returns False, that alternative is removed.
        """
        self._check_can_write()
        self._alternatives = [it for it in self._alternatives if it.and_with(merge)]

    @cython.ccall
    def copy_then_all_alternative_and_with(self, merge: GraphRequirementList) -> GraphRequirementSet:
        result = GraphRequirementSet()
        for it in self._alternatives:
            new_alt = it.copy_then_and_with(merge)
            if new_alt is not None:
                result.add_alternative(new_alt)
        return result

    @cython.ccall
    def copy_then_and_with_set(self, right: GraphRequirementSet) -> GraphRequirementSet:
        """
        Given two `GraphRequirementSet` A and B, creates a new GraphRequirementSet that is only satisfied when
        both A and B are satisfied.
        """
        if len(right._alternatives) == 1:
            result = GraphRequirementSet()
            right_req = right._alternatives[0]
            for left_alt in self._alternatives:
                new_alt = left_alt.copy_then_and_with(right_req)
                if new_alt is not None:
                    result._alternatives.append(new_alt)
            return result

        elif len(self._alternatives) == 1:
            return right.copy_then_and_with_set(self)

        else:
            result = GraphRequirementSet()

            for alt in itertools.product(self._alternatives, right._alternatives):
                new_alt = alt[0].copy_then_and_with(alt[1])
                if new_alt is not None:
                    result._alternatives.append(new_alt)

            return result

    @cython.ccall
    def copy_then_remove_entries_for_set_resources(self, resources: ResourceCollection) -> GraphRequirementSet:
        result = GraphRequirementSet()
        for alternative in self._alternatives:
            new_entry = alternative.copy_then_remove_entries_for_set_resources(resources)
            if new_entry is not None:
                # TODO: short circuit for trivial
                result._alternatives.append(new_entry)
        return result

    def optimize_alternatives(self: GraphRequirementSet) -> None:
        """Remove redundant alternatives that are supersets of other alternatives."""

        self._check_can_write()
        if len(self._alternatives) <= 1:
            return

        for alt in self._alternatives:
            if alt.num_requirements() == 0:
                # Trivial requirement - everything else is redundant
                self._alternatives = [alt]
                return

        # Sort by "complexity" - simpler requirements first (fewer total constraints)
        sorted_alternatives = sorted(self._alternatives, key=GraphRequirementList.complexity_key_for_simplify)

        result: list[GraphRequirementList] = []

        single_req_mask = Bitmask.create()

        for current in sorted_alternatives:
            case = current._single_resource_optimize_logic(single_req_mask)
            if case == 0:
                continue
            elif case == 1:
                is_superset = False
            else:
                is_superset = any(current.is_requirement_superset(existing) for existing in result)

            if not is_superset:
                # Also need to remove any existing requirements that current makes obsolete
                result = [req for req in result if not req.is_requirement_superset(current)]
                result.append(current)

        self._alternatives = result

    def __str__(self) -> str:
        if len(self._alternatives) == 1:
            return str(self._alternatives[0])
        parts = [f"({part})" for part in self._alternatives]
        if not parts:
            return "Impossible"
        return " or ".join(parts)

    @property
    def as_str(self) -> str:
        return str(self)

    @classmethod
    @functools.cache
    def trivial(cls) -> typing.Self:
        """
        A GraphRequirementSet that is always satisfied.
        """
        r = cls()
        r.add_alternative(GraphRequirementList())
        r.freeze()
        return r

    def is_trivial(self) -> cython.bint:
        return self == GraphRequirementSet.trivial()

    @classmethod
    @functools.cache
    def impossible(cls) -> typing.Self:
        """
        A GraphRequirementSet that is never satisfied.
        """
        # No alternatives makes satisfied always return False
        r = cls()
        r.freeze()
        return r

    def is_impossible(self) -> cython.bint:
        return self == GraphRequirementSet.impossible()

    @property
    def as_lines(self) -> Iterator[str]:
        if self.is_impossible():
            yield "Impossible"
        elif self.is_trivial():
            yield "Trivial"
        else:
            for alternative in self._alternatives:
                yield str(alternative)

    def pretty_print(self, indent: str = "", print_function: typing.Callable[[str], None] = logging.info) -> None:
        for line in sorted(self.as_lines):
            print_function(indent + line)

    @cython.ccall
    def isolate_damage_requirements(self, resources: ResourceCollection) -> GraphRequirementSet:
        result = GraphRequirementSet()

        for alternative in self._alternatives:
            # None means impossible
            isolated: GraphRequirementList | None = alternative.isolate_damage_requirements(resources)

            if isolated is not None:
                if isolated.equals_to(GraphRequirementSet.trivial().alternatives[0]):
                    return GraphRequirementSet.trivial()
                else:
                    result._alternatives.append(isolated)

        return result


class ProcessNodesResponse(typing.NamedTuple):
    reach_nodes: dict[int, DamageState]
    requirements_excluding_leaving_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]]
    path_to_node: dict[int, list[int]]


def _combine_damage_requirements(
    damage: float,
    requirement: GraphRequirementSet,
    satisfied_requirement: tuple[GraphRequirementSet, bool],
    resources: ResourceCollection,
) -> tuple[GraphRequirementSet, bool]:
    """
    Helper function combining damage requirements from requirement and satisfied_requirement. Other requirements are
    considered either trivial or impossible.
    :param damage:
    :param requirement:
    :param satisfied_requirement:
    :param resources:
    :return: The combined requirement and a boolean, indicating if the requirement may have non-damage components.
    """
    if damage == 0:
        # If we took no damage here, then one of the following is true:
        # - There's no damage requirement in this edge
        # - Our resources allows for alternatives with no damage requirement
        # - Our resources grants immunity to the damage resources
        # In all of these cases, we can verify that assumption with the following assertion
        # assert requirement.isolate_damage_requirements(context) == Requirement.trivial()
        #
        return satisfied_requirement

    isolated_requirement = requirement.isolate_damage_requirements(resources)
    isolated_satisfied = (
        satisfied_requirement[0].isolate_damage_requirements(resources)
        if satisfied_requirement[1]
        else satisfied_requirement[0]
    )

    if isolated_requirement == GraphRequirementSet.trivial():
        result = isolated_satisfied
    elif isolated_satisfied == GraphRequirementSet.trivial():
        result = isolated_requirement
    else:
        result = isolated_requirement.copy_then_and_with_set(isolated_satisfied)

    return result, False


@cython.ccall
def _is_damage_state_strictly_better(
    game_state: DamageState,
    target_node_index: cython.int,
    use_energy_fast_path: cython.bint,
    checked_nodes: dict[cython.int, DamageState],
    nodes_to_check: dict[int, DamageState],
) -> cython.bint:
    # a >= b -> !(b > a)
    checked_target = checked_nodes.get(target_node_index)
    if checked_target is not None:
        if use_energy_fast_path:
            if game_state._energy <= checked_target._energy:  # type: ignore[attr-defined]
                return False
        elif not game_state.is_better_than(checked_target):
            return False

    queued_target = nodes_to_check.get(target_node_index)
    if queued_target is not None:
        if use_energy_fast_path:
            if game_state._energy <= queued_target._energy:  # type: ignore[attr-defined]
                return False
        elif not game_state.is_better_than(queued_target):
            return False

    return True


@cython.locals(
    node_index=cython.int,
    target_node_index=cython.int,
    damage_health=cython.int,
    satisfied=cython.bint,
    can_leave_node=cython.bint,
    record_paths=cython.bint,
    damage=cython.float,
)
def resolver_reach_process_nodes(
    logic: Logic,
    initial_state: State,
    nodes_to_check: dict[int, DamageState],
) -> ProcessNodesResponse:
    all_nodes: Sequence[WorldGraphNode] = logic.all_nodes
    resources: ResourceCollection = initial_state.resources

    record_paths: cython.bint = logic.record_paths

    checked_nodes: dict[int, DamageState] = {}
    satisfied_requirement_on_node: dict[int, tuple[GraphRequirementSet, bool]] = {
        initial_state.node.node_index: (GraphRequirementSet.trivial(), False)
    }

    reach_nodes: dict[int, DamageState] = {}
    requirements_excluding_leaving_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]] = {}
    path_to_node: dict[int, list[int]] = {
        initial_state.node.node_index: [],
    }

    while nodes_to_check:
        node_index: cython.int = next(iter(nodes_to_check))
        node: WorldGraphNode = all_nodes[node_index]
        game_state: DamageState = nodes_to_check.pop(node_index)

        if node.heal:
            game_state = game_state.apply_node_heal(node, initial_state.resources)

        checked_nodes[node_index] = game_state
        if node_index != initial_state.node.node_index:
            reach_nodes[node_index] = game_state

        can_leave_node: cython.bint = True
        if node.require_collected_to_leave:
            can_leave_node = node.resource_gain_bitmask.is_subset_of(resources.resource_bitmask)

        for connection in node.connections:
            target_node_index: cython.int = connection[0].node_index
            requirement: GraphRequirementSet = connection[1]

            # a >= b -> !(b > a)
            if not game_state.is_better_than(checked_nodes.get(target_node_index)) or not game_state.is_better_than(
                nodes_to_check.get(target_node_index)
            ):
                continue

            satisfied: cython.bint = can_leave_node
            damage_health: cython.int = game_state.health_for_damage_requirements()

            if satisfied:
                # Check if the normal requirements to reach that node is satisfied
                satisfied = requirement.satisfied(resources, damage_health)
                if satisfied:
                    # If it is, check if we additional requirements figured out by backtracking is satisfied
                    satisfied = logic.get_additional_requirements(node).satisfied(resources, damage_health)

            if satisfied:
                damage: cython.float = requirement.damage(resources)
                nodes_to_check[target_node_index] = game_state.apply_damage(damage)

                if node.heal:
                    satisfied_requirement_on_node[target_node_index] = (requirement, True)
                else:
                    satisfied_requirement_on_node[target_node_index] = _combine_damage_requirements(
                        damage,
                        requirement,
                        satisfied_requirement_on_node[node.node_index],
                        resources,
                    )
                if record_paths:
                    path_to_node[target_node_index] = list(path_to_node[node_index])
                    path_to_node[target_node_index].append(node_index)

            else:
                # If we can't go to this node, store the reason in order to build the satisfiable requirements.
                # Note we ignore the 'additional requirements' here because it'll be added on the end.
                if not connection.requirement_without_leaving.satisfied(resources, damage_health):
                    if target_node_index not in requirements_excluding_leaving_by_node:
                        requirements_excluding_leaving_by_node[target_node_index] = []

                    requirements_excluding_leaving_by_node[target_node_index].append(
                        (
                            connection.requirement_without_leaving,
                            satisfied_requirement_on_node[node.node_index][0],
                        )
                    )

    return ProcessNodesResponse(
        reach_nodes=reach_nodes,
        requirements_excluding_leaving_by_node=requirements_excluding_leaving_by_node,
        path_to_node=path_to_node,
    )


@cython.locals(node_index=cython.int, a=GraphRequirementList, b=GraphRequirementList)
@cython.ccall
def build_satisfiable_requirements(
    logic: Logic,
    requirements_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]],
) -> frozenset[GraphRequirementList]:
    data: list[GraphRequirementList] = []

    additional_requirements_list: list[GraphRequirementSet] = logic.additional_requirements

    for node_index, reqs in requirements_by_node.items():
        set_param: set[GraphRequirementList] = set()

        for req_a, req_b in reqs:
            for alt in itertools.product(req_a.alternatives, req_b.alternatives):
                new_alt = alt[0].copy_then_and_with(alt[1])
                if new_alt is not None:
                    set_param.add(new_alt)

        additional_alts: tuple[GraphRequirementList, ...] = additional_requirements_list[node_index].alternatives
        for a in set_param:
            for b in additional_alts:
                new_list = a.copy_then_and_with(b)
                if new_list is not None:
                    data.append(new_list)

    return frozenset(data)
