# distutils: language=c++
# cython: profile=False
# pyright: reportPossiblyUnboundVariable=false
# pyright: reportReturnType=false
# mypy: disable-error-code="return"

from __future__ import annotations

import copy
import dataclasses
import functools
import logging
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping, Sequence

    # The package is named `Cython`, so in a case-sensitive system mypy fails to find cython with just `import cython`
    import Cython as cython

    from randovania.game_description.game_database_view import ResourceDatabaseView
    from randovania.game_description.resources.resource_info import ResourceGain, ResourceGainTuple, ResourceInfo
    from randovania.generator.old_generator_reach import GraphData, RustworkXGraph
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode
    from randovania.resolver.damage_state import DamageState
    from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState
    from randovania.resolver.logic import Logic
else:
    # However cython's compiler seems to expect the import to be this way, otherwise `cython.compiled` breaks
    import cython

# ruff: noqa: UP046

if cython.compiled:
    if not typing.TYPE_CHECKING:
        from cython.cimports.cpython.ref import PyObject
        from cython.cimports.libcpp.deque import deque
        from cython.cimports.libcpp.unordered_map import unordered_map
        from cython.cimports.libcpp.utility import pair
        from cython.cimports.libcpp.vector import vector
        from cython.cimports.randovania.lib.bitmask import Bitmask
else:
    from randovania._native_helper import Deque as deque
    from randovania._native_helper import Pair as pair
    from randovania._native_helper import ProcessNodesState, PyImmutableRef, PyRef
    from randovania._native_helper import UnorderedMap as unordered_map
    from randovania._native_helper import Vector as vector
    from randovania.lib.bitmask import Bitmask

    PyObject = object

    if typing.TYPE_CHECKING:
        GraphRequirementListRef = PyImmutableRef["GraphRequirementList"]
        GraphRequirementSetRef = PyRef["GraphRequirementSet"]
        ResourceInfoRef = PyImmutableRef[ResourceInfo]
    else:
        GraphRequirementListRef = PyImmutableRef
        GraphRequirementSetRef = PyRef
        ResourceInfoRef = PyImmutableRef


@cython.final
@cython.cclass
class ResourceCollection:
    resource_bitmask = cython.declare(Bitmask, visibility="public")
    _resource_array = cython.declare(vector[cython.int])
    _existing_resources: dict[int, ResourceInfo] = cython.declare(dict[int, object])  # type: ignore[arg-type]
    _damage_reduction_cache: unordered_map[cython.size_t, cython.float]
    _resource_database: ResourceDatabaseView = cython.declare(object)  # type: ignore[assignment]

    def __init__(self, resource_database: ResourceDatabaseView, resource_array: vector[cython.int]) -> None:
        self.resource_bitmask = Bitmask.create_native()
        self._resource_array = resource_array
        self._existing_resources = {}
        self._damage_reduction_cache = unordered_map[cython.size_t, cython.float]()
        self._resource_database = resource_database

    @classmethod
    def with_resource_count(cls, resource_database: ResourceDatabaseView, count: cython.size_t) -> ResourceCollection:
        result = cls(resource_database, vector[cython.int]())
        if cython.compiled:
            result._resize_array_to_fit(count)
        else:
            result._resource_array = vector([0]) * count
        return result

    @cython.ccall
    def _resize_array_to_fit(self, size: cython.size_t) -> cython.void:
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
        resource_index: cython.size_t = item.resource_index
        if resource_index < self._resource_array.size():
            return self._resource_array[resource_index]
        else:
            return 0

    @cython.ccall
    def get_index(self, resource_index: cython.size_t) -> cython.int:
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
    @cython.inline
    def has_resource(self, resource: ResourceInfo) -> cython.bint:
        return self.get(resource) > 0

    @cython.ccall
    @cython.inline
    def is_resource_set(self, resource: ResourceInfo) -> cython.bint:
        """
        Checks if the given resource has a value explicitly set, instead of using the fallback of 0.
        :param resource:
        :return:
        """
        return resource.resource_index in self._existing_resources

    def set_resource(self, resource: ResourceInfo, quantity: cython.int) -> cython.void:
        """Sets the quantity of the given resource to be exactly the given value.
        This method should be used in exceptional cases only. For common usage, use `add_resource_gain`.
        """
        quantity = max(quantity, 0)
        resource_index: cython.size_t = resource.resource_index
        self._damage_reduction_cache.clear()
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
    @cython.ccall
    def add_resource(self, resource: ResourceInfo, quantity: cython.int) -> cython.void:
        self._damage_reduction_cache.clear()

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

    @cython.locals(resource=object, quantity=cython.int)
    @cython.ccall
    @cython.inline
    def add_resource_gain(self, resource_gain: ResourceGain) -> cython.void:
        for resource, quantity in resource_gain:
            self.add_resource(resource, quantity)

    def as_resource_gain(self) -> ResourceGain:
        for index, resource in self._existing_resources.items():
            yield resource, self._resource_array[index]

    def remove_resource(self, resource: ResourceInfo) -> cython.void:
        """
        Removes the given resource, making `is_resource_set` return False for it.
        This should be used in exceptional cases only. Consider `add_resource_gain` with negative gain instead.
        """
        resource_index: cython.size_t = resource.resource_index
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
    def get_damage_reduction(self, resource_index: cython.size_t) -> cython.float:
        if cython.compiled:
            it = self._damage_reduction_cache.find(resource_index)  # type: ignore[attr-defined]
            if it != self._damage_reduction_cache.end():  # type: ignore[attr-defined]
                return cython.operator.dereference(it).second  # type: ignore[attr-defined]
        else:
            if resource_index in self._damage_reduction_cache:
                return self._damage_reduction_cache[resource_index]

        resource: ResourceInfo = getattr(self._resource_database, "_resource_mapping")[resource_index]
        reduction: cython.float = self._resource_database.get_damage_reduction(resource, self)
        self._damage_reduction_cache[resource_index] = reduction
        return reduction

    def __copy__(self) -> ResourceCollection:
        return self.duplicate()


@cython.ccall
def _is_later_progression_item(
    resource_index: cython.size_t, progressive_chain_info: None | tuple[Sequence[cython.size_t], int]
) -> bool:
    if not progressive_chain_info:
        return False
    progressive_chain, index = progressive_chain_info
    return resource_index in progressive_chain and progressive_chain.index(resource_index) > index


@cython.ccall
def _downgrade_progressive_item(
    resource_index: cython.size_t, progressive_chain_info: tuple[Sequence[cython.size_t], int]
) -> cython.size_t:
    progressive_chain, _ = progressive_chain_info
    return progressive_chain[progressive_chain.index(resource_index) - 1]


@cython.final
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
    _other_resources: unordered_map[cython.size_t, cython.int]
    _damage_resources: unordered_map[cython.size_t, cython.int]

    _resource_db: ResourceDatabaseView | None
    _frozen: cython.bint

    def __init__(self, resource_db: ResourceDatabaseView | None) -> None:
        self._set_bitmask = Bitmask.create_native()
        self._negate_bitmask = Bitmask.create_native()
        self._other_resources = unordered_map[cython.size_t, cython.int]()
        self._damage_resources = unordered_map[cython.size_t, cython.int]()

        self._resource_db = resource_db
        self._frozen = False

    @staticmethod
    @cython.cfunc
    def from_components(
        resource_db: ResourceDatabaseView | None,
        set_bitmask: Bitmask,
        negate_bitmask: Bitmask,
        other_resources: unordered_map[cython.size_t, cython.int],
        damage_resources: unordered_map[cython.size_t, cython.int],
    ) -> GraphRequirementList:
        """Alternative constructor that accepts all components directly."""
        result: GraphRequirementList = GraphRequirementList.__new__(GraphRequirementList)
        result._set_bitmask = set_bitmask
        result._negate_bitmask = negate_bitmask
        result._other_resources = other_resources
        result._damage_resources = damage_resources
        result._resource_db = resource_db
        result._frozen = False
        return result

    @staticmethod
    @cython.cfunc
    def create_empty(resource_db: ResourceDatabaseView | None) -> GraphRequirementList:
        """Fast path for creating empty instances without __init__ overhead."""
        result: GraphRequirementList = GraphRequirementList.__new__(GraphRequirementList)
        result._set_bitmask = Bitmask.create_native()
        result._negate_bitmask = Bitmask.create_native()
        if not cython.compiled:
            result._other_resources = unordered_map[cython.size_t, cython.int]()
            result._damage_resources = unordered_map[cython.size_t, cython.int]()
        result._resource_db = resource_db
        result._frozen = False
        return result

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

        # Hash the bitmasks
        result: cython.ulonglong = hash(self._set_bitmask)
        result ^= hash(self._negate_bitmask) * 31

        if cython.compiled:
            # Hash the unordered_maps using pure C arithmetic
            # Use a commutative operation (XOR) since map iteration order is unspecified
            key: cython.size_t
            value: cython.int
            hash_contribution: cython.ulonglong

            for entry in self._other_resources:
                key = entry.first
                value = entry.second
                # Combine key and value using C integer arithmetic with type casts
                hash_contribution = cython.cast(cython.ulonglong, key) * cython.cast(
                    cython.ulonglong, 0x9E3779B97F4A7C15
                )
                hash_contribution ^= cython.cast(cython.ulonglong, value) * cython.cast(
                    cython.ulonglong, 0x517CC1B727220A95
                )
                result ^= hash_contribution

            for entry in self._damage_resources:
                key = entry.first
                value = entry.second
                # Use different multipliers to distinguish from _other_resources
                hash_contribution = cython.cast(cython.ulonglong, key) * cython.cast(cython.ulonglong, 0x85EBCA6B)
                hash_contribution ^= cython.cast(cython.ulonglong, value) * cython.cast(cython.ulonglong, 0xC2B2AE35)
                result ^= hash_contribution
        else:
            # Pure Python mode: use simple tuple hashing
            result ^= hash(tuple(sorted(self._other_resources.items())))
            result ^= hash(tuple(sorted(self._damage_resources.items()))) * 37

        return hash(result)

    def _resource_mapping(self) -> dict[int, ResourceInfo]:
        if self._resource_db is None:
            return {}
        return getattr(self._resource_db, "_resource_mapping")

    @cython.ccall
    @cython.inline
    def is_frozen(self) -> cython.bint:
        """Returns True if `freeze` was previously called."""
        return self._frozen

    @cython.ccall
    @cython.inline
    def freeze(self) -> cython.void:
        """Prevents any further modifications to this GraphRequirementList. Copies won't be frozen."""
        self._frozen = True

    @cython.cfunc
    @cython.inline
    def _check_can_write(self) -> cython.void:
        if self._frozen:
            raise RuntimeError("Cannot modify a frozen GraphRequirementList")

    @cython.cfunc
    @cython.inline
    def _complexity_key_for_simplify(self) -> tuple[int, int, int]:
        """
        A value that indicates how "complex" this requirement is. Used for sorting the alternatives in
        GraphRequirementSet.optimize_alternatives
        """
        return (
            self._set_bitmask.num_set_bits() + self._negate_bitmask.num_set_bits(),
            self._other_resources.size(),
            self._damage_resources.size(),
        )

    def __copy__(self) -> GraphRequirementList:
        result = GraphRequirementList.create_empty(self._resource_db)
        result._set_bitmask = self._set_bitmask.copy()
        result._negate_bitmask = self._negate_bitmask.copy()
        result._other_resources = copy.copy(self._other_resources)
        result._damage_resources = copy.copy(self._damage_resources)

        return result

    def __str__(self) -> str:
        mapping = self._resource_mapping()

        parts = sorted(
            f"{mapping[resource_index].resource_type.non_negated_prefix}{mapping[resource_index]}"
            for resource_index in self._set_bitmask.get_set_bits()
            if not self._other_resources.contains(resource_index)
        )
        parts.extend(
            sorted(
                f"{mapping[resource_index].resource_type.negated_prefix}{mapping[resource_index]}"
                for resource_index in self._negate_bitmask.get_set_bits()
            )
        )
        parts.extend(sorted(f"{mapping[entry.first]} ≥ {entry.second}" for entry in self._other_resources))
        parts.extend(sorted(f"{mapping[entry.first]} ≥ {entry.second}" for entry in self._damage_resources))
        if parts:
            return " and ".join(parts)
        else:
            return "Trivial"

    @cython.ccall
    @cython.inline
    def num_requirements(self) -> cython.int:
        """Returns the total number of resource requirements in this list."""
        return self._set_bitmask.num_set_bits() + self._negate_bitmask.num_set_bits() + len(self._damage_resources)

    @cython.ccall
    @cython.inline
    def is_trivial(self) -> cython.bint:
        """Returns True if this requirement is trivial (always satisfied)."""
        return (
            self._set_bitmask.is_empty()
            and self._negate_bitmask.is_empty()
            and self._other_resources.empty()
            and self._damage_resources.empty()
        )

    @cython.ccall
    @cython.inline
    def all_resources(self, *, include_damage: cython.bint = True) -> set[ResourceInfo]:
        """Returns a set of all resources involved in this requirement."""
        mapping = self._resource_mapping()
        result = set()

        resource_index: cython.size_t
        for resource_index in self._set_bitmask.get_set_bits():
            result.add(mapping[resource_index])
        for resource_index in self._negate_bitmask.get_set_bits():
            result.add(mapping[resource_index])
        if include_damage:
            for entry in self._damage_resources:
                result.add(mapping[entry.first])
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
        resource_index: cython.size_t = resource.resource_index
        return self.get_requirement_for_index(resource_index, include_damage)

    @cython.ccall
    def get_requirement_for_index(
        self, resource_index: cython.size_t, include_damage: cython.bint = True
    ) -> tuple[cython.int, cython.bint]:
        """
        Gets the amount and negate status for the given resource. Damage resources are ignored.
        :param resource:
        :return: A tuple, containing the amount and if it's a negate requirement.
        """

        if self._other_resources.contains(resource_index):
            return self._other_resources[resource_index], False

        if self._set_bitmask.is_set(resource_index):
            return 1, False

        if self._negate_bitmask.is_set(resource_index):
            return 1, True

        if include_damage and self._damage_resources.contains(resource_index):
            return self._damage_resources[resource_index], False

        return 0, False

    @cython.ccall
    # @cython.exceptval(check=False)
    def satisfied(self, resources: ResourceCollection, health: cython.float) -> cython.bint:
        """Checks if the given resources and health satisfies this requirement."""
        if not self._set_bitmask.is_subset_of(resources.resource_bitmask):
            return False

        if not self._negate_bitmask.is_empty():
            if self._negate_bitmask.is_subset_of(resources.resource_bitmask):
                return False

        for entry in self._other_resources:
            if resources.get_index(entry.first) < entry.second:
                return False

        for entry in self._damage_resources:
            health -= entry.second * resources.get_damage_reduction(entry.first)
            if health <= 0:
                return False

        return True

    @cython.ccall
    # @cython.exceptval(check=False)
    def damage(self, resources: ResourceCollection) -> cython.float:
        """
        How much damage this requirement causes with the reductions of the given resources.
        This ignores all other requirements.
        """
        result: cython.float = 0

        for entry in self._damage_resources:
            result += entry.second * resources.get_damage_reduction(entry.first)
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

        self._set_bitmask.union(merge._set_bitmask)
        self._negate_bitmask.union(merge._negate_bitmask)

        for entry in merge._other_resources:
            if self._other_resources.contains(entry.first):
                self._other_resources[entry.first] = max(self._other_resources[entry.first], entry.second)
            else:
                self._other_resources[entry.first] = entry.second

        for entry in merge._damage_resources:
            if self._damage_resources.contains(entry.first):
                self._damage_resources[entry.first] += entry.second
            else:
                self._damage_resources[entry.first] = entry.second

        return True

    @cython.ccall
    def copy_then_and_with(self, right: GraphRequirementList) -> GraphRequirementList | None:
        """
        Copies this requirement and then performs `and_with`, but more efficiently.
        Returns None if the combination is impossible to satisfy (mix of set and negate requirements).
        """
        db = self._resource_db
        if db is None:
            db = right._resource_db

        if cython.compiled:
            result = GraphRequirementList.from_components(
                db,
                self._set_bitmask.copy(),
                self._negate_bitmask.copy(),
                self._other_resources,
                self._damage_resources,
            )
        else:
            result = GraphRequirementList.from_components(
                db,
                self._set_bitmask.copy(),
                self._negate_bitmask.copy(),
                copy.copy(self._other_resources),
                copy.copy(self._damage_resources),
            )

        # Copy and union bitmasks
        result._set_bitmask.union(right._set_bitmask)
        result._negate_bitmask.union(right._negate_bitmask)

        # Check if there's any conflict between set and negate requirements
        if result._set_bitmask.share_at_least_one_bit(result._negate_bitmask):
            return None

        for entry in right._other_resources:
            if result._other_resources.contains(entry.first):
                result._other_resources[entry.first] = max(result._other_resources[entry.first], entry.second)
            else:
                result._other_resources[entry.first] = entry.second

        for entry in right._damage_resources:
            if result._damage_resources.contains(entry.first):
                result._damage_resources[entry.first] += entry.second
            else:
                result._damage_resources[entry.first] = entry.second

        return result

    @cython.ccall
    def copy_then_remove_entries_for_set_resources(self, resources: ResourceCollection) -> GraphRequirementList | None:
        from randovania.game_description.resources.item_resource_info import ItemResourceInfo

        result = GraphRequirementList.create_empty(self._resource_db)

        for resource in self.all_resources(include_damage=False):
            amount, negate = self.get_requirement_for(resource)
            if resources.is_resource_set(resource):
                satisfied: cython.bint
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

        for entry in self._damage_resources:
            result.add_damage(entry.first, entry.second)

        return result

    @cython.ccall
    def add_resource(self, resource: ResourceInfo, amount: cython.int, negate: cython.bint) -> cython.void:
        """
        Adds a new resource requirement to this.
        If negate is set, amount must be 1.
        """
        self._resource_mapping()[resource.resource_index] = resource
        if resource.resource_type.is_damage():
            self.add_damage(resource.resource_index, amount)
        else:
            self.add_resource_index(resource.resource_index, amount, negate)

    @cython.ccall
    def add_resource_index(self, resource_index: cython.int, amount: cython.int, negate: cython.bint) -> cython.void:
        """
        Adds a new resource requirement to this.
        If negate is set, amount must be 1.
        """
        self._check_can_write()

        if amount == 0:
            return  # type: ignore[return-value]

        assert not negate or amount == 1

        if negate:
            target_bitmask = self._negate_bitmask
            other_bitmask = self._set_bitmask
        else:
            target_bitmask = self._set_bitmask
            other_bitmask = self._negate_bitmask

        if other_bitmask.is_set(resource_index):
            raise ValueError("Cannot add resource requirement that conflicts with existing requirements")

        target_bitmask.set_bit(resource_index)
        if amount > 1:
            if self._other_resources.contains(resource_index):
                self._other_resources[resource_index] = max(self._other_resources[resource_index], amount)
            else:
                self._other_resources[resource_index] = amount

    @cython.ccall
    def add_damage(self, resource_index: cython.int, amount: cython.int) -> cython.void:
        self._check_can_write()
        if self._damage_resources.contains(resource_index):
            self._damage_resources[resource_index] += amount
        else:
            self._damage_resources[resource_index] = amount

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

        for entry in self._other_resources:
            if resources.get_index(entry.first) < entry.second:
                return None

        if self._damage_resources.empty():
            return _trivial_list

        result = GraphRequirementList.create_empty(self._resource_db)

        for entry in self._damage_resources:
            if resources.get_damage_reduction(entry.first) == 0:
                return GraphRequirementList.create_empty(self._resource_db)

            result._damage_resources[entry.first] = entry.second
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
        for entry in subset_req._other_resources:
            if not self._other_resources.contains(entry.first) or self._other_resources[entry.first] < entry.second:
                return False

        # Check _damage_resources - superset must have >= amounts for all damage in subset
        for entry in subset_req._damage_resources:
            if not self._damage_resources.contains(entry.first) or self._damage_resources[entry.first] < entry.second:
                return False

        # Remove duplicates
        return True

    @cython.cfunc
    def _simplify_handle_resource(
        self,
        resource_index: cython.size_t,
        amount: cython.int,
        negate: cython.bint,
        progressive_item_info: None | tuple[Sequence[cython.size_t], int],
    ) -> cython.void:
        if _is_later_progression_item(resource_index, progressive_item_info):
            assert progressive_item_info is not None
            self.add_resource_index(
                _downgrade_progressive_item(resource_index, progressive_item_info),
                1,
                False,
            )
        else:
            self.add_resource_index(resource_index, amount, negate)

    @cython.ccall
    def simplify_requirement_list(
        self,
        resources: ResourceCollection,
        health_for_damage_requirements: cython.float,
        node_resources: Sequence[cython.size_t],
        progressive_item_info: None | tuple[Sequence[cython.size_t], int],
    ) -> GraphRequirementList | None:
        """Used by resolver.py for `_simplify_additional_requirement_set`"""

        result = GraphRequirementList.create_empty(self._resource_db)
        something_set: cython.bint = False

        for resource_index in self._set_bitmask.get_set_bits():
            amount = self._other_resources[resource_index] if self._other_resources.contains(resource_index) else 1
            if resources.get_index(resource_index) >= amount:
                continue
            result._simplify_handle_resource(resource_index, amount, False, progressive_item_info)
            something_set = True

        for resource_index in self._negate_bitmask.get_set_bits():
            if resources.get_index(resource_index) == 0:
                continue
            if resource_index in node_resources:
                return None
            result._simplify_handle_resource(resource_index, 1, True, progressive_item_info)
            something_set = True

        if self.damage(resources) >= health_for_damage_requirements:
            something_set = True
            for entry in self._damage_resources:
                result._damage_resources[entry.first] = entry.second

        if not something_set:
            return None

        return result

    @cython.cfunc
    @cython.inline
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


_trivial_list: GraphRequirementList = GraphRequirementList(None)
_trivial_list.freeze()


@cython.final
@cython.cclass
class GraphRequirementSet:
    """
    Contains a list of GraphRequirement, but only one needs to be satisfied (OR).

    These two classes together represents a `Requirement` in disjunctive normal form.
    """

    _alternatives: vector[GraphRequirementListRef]
    _frozen: cython.bint

    def __init__(self) -> None:
        self._alternatives = vector[GraphRequirementListRef]()
        self._frozen = False

    @cython.cfunc
    @cython.inline
    @staticmethod
    def create_empty() -> GraphRequirementSet:
        """Fast path for creating empty instances without __init__ overhead."""
        result: GraphRequirementSet = GraphRequirementSet.__new__(GraphRequirementSet)
        if not cython.compiled:
            result._alternatives = vector[GraphRequirementListRef]()
        result._frozen = False
        return result

    def __copy__(self) -> GraphRequirementSet:
        result = GraphRequirementSet.create_empty()
        for it in self._alternatives:
            result._alternatives.push_back(GraphRequirementListRef(copy.copy(it.get())))
        return result

    __hash__ = None  # type: ignore[assignment]

    def __eq__(self, other: object) -> cython.bint:
        if isinstance(other, GraphRequirementSet):
            return self.equals_to(other)
        return False

    @cython.ccall
    # @cython.exceptval(check=False)
    def equals_to(self, other: GraphRequirementSet) -> cython.bint:
        if self._alternatives.size() != other._alternatives.size():
            return False
        for idx in range(self._alternatives.size()):
            if self._alternatives[idx].get() != other._alternatives[idx].get():
                return False
        return True

    @cython.inline
    @cython.ccall
    def is_frozen(self) -> cython.bint:
        """Returns True if `freeze` was previously called."""
        return self._frozen

    @cython.inline
    @cython.ccall
    def freeze(self) -> None:
        """Prevents any further modifications to this GraphRequirementSet and any nested GraphRequirementList."""
        self._frozen = True
        for it in self._alternatives:
            it.get().freeze()

    @cython.inline
    @cython.cfunc
    def _check_can_write(self) -> cython.void:
        if self._frozen:
            raise RuntimeError("Cannot modify a frozen GraphRequirementSet")

    @cython.inline
    @cython.ccall
    def num_alternatives(self) -> cython.int:
        return self._alternatives.size()

    @property
    def alternatives(self) -> Sequence[GraphRequirementList]:
        return [it.get() for it in self._alternatives]

    @cython.ccall
    @cython.inline
    def get_alternative(self, index: cython.int) -> GraphRequirementList:
        return self._alternatives[index].get()

    @cython.ccall
    @cython.inline
    def add_alternative(self, alternative: GraphRequirementList) -> cython.void:
        self._check_can_write()
        self._alternatives.push_back(GraphRequirementListRef(alternative))

    @cython.ccall
    @cython.inline
    def extend_alternatives(self, alternatives: Iterable[GraphRequirementList]) -> cython.void:
        self._check_can_write()
        for it in alternatives:
            self._alternatives.push_back(GraphRequirementListRef(it))

    @cython.ccall
    # @cython.exceptval(check=False)
    def satisfied(self, resources: ResourceCollection, energy: cython.float) -> cython.bint:
        """Checks if the given resources and health satisfies at least one alternative."""

        if cython.compiled:
            for alt in self._alternatives:
                if cython.cast(GraphRequirementList, alt.raw()).satisfied(resources, energy):
                    return True
        else:
            for alt in self._alternatives:
                if alt.get().satisfied(resources, energy):
                    return True

        return False

    @cython.ccall
    # @cython.exceptval(check=False)
    def damage(self, resources: ResourceCollection) -> cython.float:
        """
        The least amount of damage from any alternative.
        """
        damage: cython.float = float("inf")

        for alt in self._alternatives:
            new_dmg: cython.float = cython.cast(GraphRequirementList, alt.raw()).damage(resources)
            if new_dmg <= 0.0:
                return new_dmg
            if new_dmg < damage:
                damage = new_dmg

        return damage

    @cython.ccall
    def all_alternative_and_with(self, merge: GraphRequirementList) -> cython.void:
        """
        Calls `and_with` for every alternative.
        If `and_with` returns False, that alternative is removed.
        """
        self._check_can_write()

        idx: cython.size_t
        for idx in range(self._alternatives.size() - 1, -1, -1):
            if not cython.cast(GraphRequirementList, self._alternatives[idx].raw()).and_with(merge):
                self._alternatives.erase(self._alternatives.begin() + idx)

    @cython.ccall
    def copy_then_all_alternative_and_with(self, merge: GraphRequirementList) -> GraphRequirementSet:
        result = GraphRequirementSet.create_empty()
        for it in self._alternatives:
            new_alt = cython.cast(GraphRequirementList, it.raw()).copy_then_and_with(merge)
            if new_alt is not None:
                result.add_alternative(new_alt)
        return result

    @cython.ccall
    def copy_then_and_with_set(self, right: GraphRequirementSet) -> GraphRequirementSet:
        """
        Given two `GraphRequirementSet` A and B, creates a new GraphRequirementSet that is only satisfied when
        both A and B are satisfied.
        """
        result: GraphRequirementSet
        if right._alternatives.size() == 1:
            result = GraphRequirementSet.create_empty()
            right_req = right._alternatives[0]
            for left_alt in self._alternatives:
                new_alt = cython.cast(GraphRequirementList, left_alt.raw()).copy_then_and_with(
                    cython.cast(GraphRequirementList, right_req.raw())
                )
                if new_alt is not None:
                    result._alternatives.push_back(GraphRequirementListRef(new_alt))
            return result

        elif self._alternatives.size() == 1:
            return right.copy_then_and_with_set(self)

        else:
            result = GraphRequirementSet.create_empty()

            for left_alt in self._alternatives:
                for right_alt in right._alternatives:
                    new_alt = cython.cast(GraphRequirementList, left_alt.raw()).copy_then_and_with(
                        cython.cast(GraphRequirementList, right_alt.raw())
                    )
                    if new_alt is not None:
                        result._alternatives.push_back(GraphRequirementListRef(new_alt))

            return result

    @cython.ccall
    def copy_then_remove_entries_for_set_resources(self, resources: ResourceCollection) -> GraphRequirementSet:
        result = GraphRequirementSet.create_empty()
        for alternative in self._alternatives:
            new_entry = alternative.get().copy_then_remove_entries_for_set_resources(resources)
            if new_entry is not None:
                # TODO: short circuit for trivial
                result._alternatives.push_back(GraphRequirementListRef(new_entry))
        return result

    @cython.ccall
    def optimize_alternatives(self: GraphRequirementSet) -> cython.void:
        """Remove redundant alternatives that are supersets of other alternatives."""

        self._check_can_write()
        if self._alternatives.size() <= 1:
            return  # type: ignore[return-value]

        for alt in self._alternatives:
            if alt.get().num_requirements() == 0:
                # Trivial requirement - everything else is redundant
                self._alternatives.clear()
                self._alternatives.push_back(alt)
                return  # type: ignore[return-value]

        # Sort by "complexity" - simpler requirements first (fewer total constraints)
        sorted_alternatives = sorted(self.alternatives, key=GraphRequirementList._complexity_key_for_simplify)

        result: list[GraphRequirementList] = []

        single_req_mask = Bitmask.create_native()

        current: GraphRequirementList
        existing: GraphRequirementList

        for current in sorted_alternatives:
            case = current._single_resource_optimize_logic(single_req_mask)
            if case == 0:
                continue
            elif case == 1:
                is_superset = False
            else:
                is_superset = False
                for existing in result:
                    if current.is_requirement_superset(existing):
                        is_superset = True
                        break

            if not is_superset:
                # Also need to remove any existing requirements that current makes obsolete
                result = [req for req in result if not req.is_requirement_superset(current)]
                result.append(current)

        self._alternatives.clear()
        for it in result:
            self._alternatives.push_back(GraphRequirementListRef(it))

    def __str__(self) -> str:
        if self._alternatives.size() == 1:
            return str(self._alternatives[0].get())
        parts = [f"({part.get()})" for part in self._alternatives]
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
        r.add_alternative(GraphRequirementList(None))
        r.freeze()
        return r

    @cython.ccall
    def is_trivial(self) -> cython.bint:
        if self._alternatives.size() == 1:
            return self._alternatives[0].get().is_trivial()
        return False

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

    @cython.ccall
    def is_impossible(self) -> cython.bint:
        return self._alternatives.empty()

    @property
    def as_lines(self) -> Iterator[str]:
        if self.is_impossible():
            yield "Impossible"
        elif self.is_trivial():
            yield "Trivial"
        else:
            for alternative in self._alternatives:
                yield str(alternative.get())

    def pretty_print(self, indent: str = "", print_function: typing.Callable[[str], None] = logging.info) -> None:
        for line in sorted(self.as_lines):
            print_function(indent + line)

    @cython.ccall
    def isolate_damage_requirements(self, resources: ResourceCollection) -> GraphRequirementSet:
        result = GraphRequirementSet.create_empty()

        for alternative in self._alternatives:
            # None means impossible
            isolated: GraphRequirementList | None = cython.cast(
                GraphRequirementList, alternative.raw()
            ).isolate_damage_requirements(resources)

            if isolated is not None:
                if isolated.is_trivial():
                    result._alternatives.clear()
                    result._alternatives.push_back(GraphRequirementListRef(isolated))
                    break
                else:
                    result._alternatives.push_back(GraphRequirementListRef(isolated))

        return result


@cython.final
@cython.cclass
@dataclasses.dataclass()
class WorldGraphNodeConnection:
    target: cython.int
    """The destination node for this connection."""

    requirement: GraphRequirementSet
    """The requirements for crossing this connection, with all extras already processed."""

    requirement_with_self_dangerous: GraphRequirementSet
    """`requirement` combined with any resources provided by the source node that are dangerous."""

    requirement_without_leaving: GraphRequirementSet
    """
    The requirements for crossing this connection, but excluding the nodes `requirement_to_leave`.
    Useful for the resolver to calculate satisfiable requirements on rollback.
    """

    @classmethod
    def trivial(cls, target: WorldGraphNode) -> WorldGraphNodeConnection:
        trivial_requirement = GraphRequirementSet.trivial()
        return cls(
            target.node_index,
            trivial_requirement,
            trivial_requirement,
            trivial_requirement,
        )


class ProcessNodesResponse(typing.NamedTuple):
    reach_nodes: dict[int, int]
    requirements_excluding_leaving_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]]
    path_to_node: dict[int, list[int]]


@cython.cfunc
def _combine_damage_requirements(
    damage: float,
    requirement: GraphRequirementSet,
    resources: ResourceCollection,
    state_ptr: cython.pointer[ProcessNodesState],
    input_index: cython.int,
    output_index: cython.int,
) -> None:
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
        state_ptr[0].satisfied_requirement_on_node[output_index] = state_ptr[0].satisfied_requirement_on_node[
            input_index
        ]
        return

    isolated_requirement: GraphRequirementSet = requirement.isolate_damage_requirements(resources)
    isolated_satisfied: GraphRequirementSet | None = state_ptr[0].satisfied_requirement_on_node[input_index].first.get()
    assert isolated_satisfied is not None

    should_isolate_satisfied: cython.bint = state_ptr[0].satisfied_requirement_on_node[input_index].second
    if should_isolate_satisfied:
        isolated_satisfied = isolated_satisfied.isolate_damage_requirements(resources)

    # do `isolated_requirement` and `isolated_satisfied`, but figure out how to avoid the expensive operation
    result: GraphRequirementSet
    if isolated_requirement.is_trivial():
        result = isolated_satisfied
    elif isolated_satisfied.is_trivial():
        result = isolated_requirement
    else:
        # Neither side is trivial, but one alternative is the majority of the time and that path can avoid copy
        if isolated_satisfied.num_alternatives() == 1:
            # `isolated_requirement` is always the result of `isolate_damage_requirements`, so a new, mutable, copy.
            # (or trivial, but that case is above)
            isolated_requirement.all_alternative_and_with(isolated_satisfied._alternatives[0].get())
            result = isolated_requirement

        elif isolated_requirement.num_alternatives() == 1:
            if should_isolate_satisfied:
                # Same as `isolated_requirement` above
                result = isolated_satisfied
                isolated_satisfied.all_alternative_and_with(isolated_requirement.get_alternative(0))
            else:
                # But it's already been isolated before and stored in satisfied_requirement_on_node
                # so don't modify it. Still faster than the full copy_then_and_with_set
                result = isolated_satisfied.copy_then_all_alternative_and_with(isolated_requirement.get_alternative(0))
        else:
            result = isolated_requirement.copy_then_and_with_set(isolated_satisfied)

    state_ptr[0].satisfied_requirement_on_node[output_index].first.set(result)
    state_ptr[0].satisfied_requirement_on_node[output_index].second = False


@cython.cfunc
def _generic_is_damage_state_strictly_better(
    game_state: DamageState,
    target_node_index: cython.int,
    state_ptr: cython.pointer[ProcessNodesState],
) -> cython.bint:
    # a >= b -> !(b > a)
    if not game_state.is_better_than(state_ptr[0].checked_nodes[target_node_index]):
        return False

    if not game_state.is_better_than(state_ptr[0].game_states_to_check[target_node_index]):
        return False

    return True


@cython.exceptval(check=False)
@cython.cfunc
def _energy_is_damage_state_strictly_better(
    damage_health: cython.float,
    target_node_index: cython.int,
    state_ptr: cython.pointer[ProcessNodesState],
) -> cython.bint:
    # a >= b -> !(b > a)
    if damage_health <= state_ptr[0].checked_nodes[target_node_index]:
        return False

    if damage_health <= state_ptr[0].game_states_to_check[target_node_index]:
        return False

    return True


if not cython.compiled:

    def _pure_energy_is_damage_state_strictly_better(
        damage_health: cython.float,
        target_node_index: cython.int,
        state: ProcessNodesState,
    ) -> cython.bint:
        if damage_health <= state.checked_nodes[target_node_index]:
            return False

        if damage_health <= state.game_states_to_check[target_node_index]:
            return False

        return True


def resolver_reach_process_nodes(
    logic: Logic,
    initial_state: State,
) -> ProcessNodesResponse:
    all_nodes: Sequence[WorldGraphNode] = logic.all_nodes
    resources: ResourceCollection = initial_state.resources
    initial_game_state: EnergyTankDamageState = initial_state.damage_state  # type: ignore[assignment]
    resource_bitmask: Bitmask = resources.resource_bitmask
    additional_requirements_list: list[GraphRequirementSet] = logic.additional_requirements

    record_paths: cython.bint = logic.record_paths
    initial_node_index: cython.int = initial_state.node.node_index

    state: ProcessNodesState = ProcessNodesState()
    state.checked_nodes.resize(len(all_nodes), -1)
    state.nodes_to_check.push_back(initial_node_index)
    state.game_states_to_check.resize(len(all_nodes), -1)

    state_ptr: cython.pointer[ProcessNodesState]
    if cython.compiled:
        state.satisfied_requirement_on_node.resize(
            len(all_nodes), pair[GraphRequirementSetRef, cython.bint](GraphRequirementSetRef(), False)
        )
        state_ptr = cython.address(state)  # type: ignore[assignment]
    else:
        # Pure Mode cheats and uses different containers completely
        state_ptr = [state]  # type: ignore[assignment]

    state.game_states_to_check[initial_node_index] = initial_game_state.health_for_damage_requirements()
    state.satisfied_requirement_on_node[initial_node_index].first.set(GraphRequirementSet.trivial())

    found_node_order: vector[cython.size_t] = vector[cython.size_t]()
    requirements_excluding_leaving_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]] = {}
    path_to_node: dict[int, list[int]] = {
        initial_node_index: [],
    }

    # Fast path detection for EnergyTankDamageState
    use_energy_fast_path: cython.bint = hasattr(initial_game_state, "_energy")
    fast_path_maximum_energy: cython.int = 0
    if use_energy_fast_path:
        fast_path_maximum_energy = initial_game_state._maximum_energy(resources)

    while not state.nodes_to_check.empty():
        node_index: cython.int = state.nodes_to_check[0]
        state.nodes_to_check.pop_front()

        damage_health_int: cython.int = state.game_states_to_check[node_index]
        damage_health: cython.float = damage_health_int
        state.game_states_to_check[node_index] = -1

        node: WorldGraphNode = all_nodes[node_index]
        node_heal: cython.bint = node.heal
        current_game_state: DamageState

        if use_energy_fast_path:
            if node_heal:
                damage_health = damage_health_int = fast_path_maximum_energy
        else:
            if node_heal:
                current_game_state = initial_game_state.apply_node_heal(node, resources)
                damage_health = damage_health_int = current_game_state.health_for_damage_requirements()
            else:
                current_game_state = initial_game_state.with_health(damage_health_int)

        found_node_order.push_back(node_index)
        state.checked_nodes[node_index] = damage_health_int

        can_leave_node: cython.bint = True
        if node.require_collected_to_leave:
            resource_gain_bitmask: Bitmask = node.resource_gain_bitmask
            can_leave_node = resource_gain_bitmask.is_subset_of(resource_bitmask)

        node_connections: list[WorldGraphNodeConnection] = node.connections
        connection: WorldGraphNodeConnection
        for connection in node_connections:
            target_node_index: cython.int = connection.target
            requirement: GraphRequirementSet = connection.requirement

            if use_energy_fast_path:
                if cython.compiled:
                    if not _energy_is_damage_state_strictly_better(damage_health, target_node_index, state_ptr):
                        continue
                else:
                    if not _pure_energy_is_damage_state_strictly_better(damage_health, target_node_index, state):
                        continue
            else:
                if not _generic_is_damage_state_strictly_better(current_game_state, target_node_index, state_ptr):
                    continue

            satisfied: cython.bint = can_leave_node

            if satisfied:
                # Check if the normal requirements to reach that node is satisfied
                satisfied = requirement.satisfied(resources, damage_health)
                if satisfied:
                    # If it is, check if we additional requirements figured out by backtracking is satisfied
                    additional_list: GraphRequirementSet = additional_requirements_list[node_index]
                    satisfied = additional_list.satisfied(resources, damage_health)

            if satisfied:
                if state.game_states_to_check[target_node_index] < 0:
                    state.nodes_to_check.push_back(target_node_index)

                damage: cython.float = requirement.damage(resources)
                if damage <= 0:
                    state.game_states_to_check[target_node_index] = damage_health_int
                elif use_energy_fast_path:
                    damage_int: cython.int = int(damage)
                    state.game_states_to_check[target_node_index] = max(damage_health_int - damage_int, 0)
                else:
                    state.game_states_to_check[target_node_index] = current_game_state.apply_damage(
                        damage
                    ).health_for_damage_requirements()

                if node_heal:
                    state.satisfied_requirement_on_node[target_node_index].first.set(requirement)
                    state.satisfied_requirement_on_node[target_node_index].second = True
                else:
                    _combine_damage_requirements(
                        damage,
                        requirement,
                        resources,
                        state_ptr,
                        node_index,
                        target_node_index,
                    )
                if record_paths:
                    path_to_node[target_node_index] = list(path_to_node[node_index])
                    path_to_node[target_node_index].append(node_index)

            else:
                # If we can't go to this node, store the reason in order to build the satisfiable requirements.
                # Note we ignore the 'additional requirements' here because it'll be added on the end.
                if not cython.cast(GraphRequirementSet, connection.requirement_without_leaving).satisfied(
                    resources, damage_health
                ):
                    target_node_index_py: int = target_node_index
                    if target_node_index_py not in requirements_excluding_leaving_by_node:
                        requirements_excluding_leaving_by_node[target_node_index_py] = []

                    new_set: GraphRequirementSet | None = state.satisfied_requirement_on_node[node_index].first.get()
                    assert new_set is not None
                    requirements_excluding_leaving_by_node[target_node_index_py].append(
                        (connection.requirement_without_leaving, new_set)
                    )

    reach_nodes: dict[int, int] = {
        node_index: state.checked_nodes[node_index]
        for node_index in found_node_order
        if node_index != initial_node_index
    }

    return ProcessNodesResponse(
        reach_nodes=reach_nodes,
        requirements_excluding_leaving_by_node=requirements_excluding_leaving_by_node,
        path_to_node=path_to_node,
    )


@cython.locals(node_index=cython.int)
@cython.ccall
def build_satisfiable_requirements(
    logic: Logic,
    requirements_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]],
) -> frozenset[GraphRequirementList]:
    data: list[GraphRequirementList] = []

    additional_requirements_list: list[GraphRequirementSet] = logic.additional_requirements

    for node_index, reqs in requirements_by_node.items():
        set_param: set[GraphRequirementList] = set()
        new_list: GraphRequirementList | None

        for idx in range(len(reqs)):
            entry: tuple[GraphRequirementSet, GraphRequirementSet] = reqs[idx]
            req_a: GraphRequirementSet = entry[0]
            req_b: GraphRequirementSet = entry[1]
            for a_ref in req_a._alternatives:
                for b_ref in req_b._alternatives:
                    new_list = a_ref.get().copy_then_and_with(b_ref.get())
                    if new_list is not None:
                        set_param.add(new_list)

        additional: GraphRequirementSet = additional_requirements_list[node_index]
        for a in set_param:
            for b in additional._alternatives:
                new_list = a.copy_then_and_with(b.get())
                if new_list is not None:
                    data.append(new_list)

    return frozenset(data)


class _NativeGraphPathDef(typing.NamedTuple):
    previous_node: cython.int
    node: cython.int
    requirement: GraphRequirementSet | cython.pointer[PyObject]


if cython.compiled:
    _NativeGraphPath = cython.struct(
        previous_node=cython.int,
        node=cython.int,
        requirement=cython.pointer[PyObject],
    )

    @cython.cfunc
    def _get_requirement_from_path(path: _NativeGraphPath) -> GraphRequirementSet:  # type: ignore[valid-type]
        return cython.cast(GraphRequirementSet, path.requirement)  # type: ignore[attr-defined]

else:
    _NativeGraphPath = _NativeGraphPathDef

    def _get_requirement_from_path(path: _NativeGraphPathDef) -> GraphRequirementSet:
        return path.requirement  # type: ignore[return-value]


def generator_reach_expand_graph(
    state: State,
    world_graph: WorldGraph,
    digraph: RustworkXGraph,
    unreachable_paths: dict[tuple[int, int], GraphRequirementSet],
    uncollectable_nodes: dict[int, GraphRequirementSet],
    *,
    for_initial_state: cython.bint,
    possible_edges: set[tuple[cython.int, cython.int]],
) -> None:
    # print("!! _expand_graph", len(paths_to_check))

    health: cython.float = state.health_for_damage_requirements
    resources = state.resources
    all_nodes = world_graph.nodes

    paths_to_check: deque[_NativeGraphPath] = deque[_NativeGraphPath]()  # type: ignore[valid-type]
    resource_nodes_to_check: set[cython.int] = set()

    previous_node: cython.int
    requirement: GraphRequirementSet

    if for_initial_state:
        requirement = GraphRequirementSet.trivial()
        paths_to_check.push_back(
            _NativeGraphPath(
                -1,
                state.node.node_index,
                cython.cast(cython.pointer[PyObject], requirement) if cython.compiled else requirement,
            )
        )

    # Check if we can expand the corners of our graph
    for edge in possible_edges:
        edge_requirement = unreachable_paths.get(edge)
        if edge_requirement is not None and edge_requirement.satisfied(resources, health):
            paths_to_check.push_back(
                _NativeGraphPath(
                    edge[0],
                    edge[1],
                    cython.cast(cython.pointer[PyObject], edge_requirement) if cython.compiled else edge_requirement,
                )
            )
            del unreachable_paths[edge]

    while not paths_to_check.empty():
        path = paths_to_check[0]
        paths_to_check.pop_front()

        previous_node = path.previous_node  # type: ignore[attr-defined]
        current_node_index: cython.int = path.node  # type: ignore[attr-defined]

        if previous_node >= 0 and digraph.has_edge(previous_node, current_node_index):
            continue

        digraph.add_node(current_node_index)
        if previous_node >= 0:
            digraph.add_edge(previous_node, current_node_index, data=_get_requirement_from_path(path))

        node: WorldGraphNode = all_nodes[current_node_index]
        if node.has_resources:
            resource_nodes_to_check.add(current_node_index)

        for connection in node.connections:
            target_node_index: cython.int = connection.target
            requirement = connection.requirement_with_self_dangerous

            if digraph.graph.has_edge(current_node_index, target_node_index):
                continue

            if requirement.satisfied(resources, health):
                # print("* Queue path to", target_node.full_name())
                paths_to_check.push_back(
                    _NativeGraphPath(
                        current_node_index,
                        target_node_index,
                        cython.cast(cython.pointer[PyObject], requirement) if cython.compiled else requirement,
                    )
                )
            else:
                unreachable_paths[current_node_index, target_node_index] = requirement
        # print("> done")

    for node_index in sorted(resource_nodes_to_check):
        requirement = all_nodes[node_index].requirement_to_collect
        if not requirement.satisfied(resources, health):
            uncollectable_nodes[node_index] = requirement


def generator_reach_find_strongly_connected_components_for(
    digraph: RustworkXGraph,
    node_index: cython.int,
) -> Sequence[int]:
    """Finds the strongly connected component with the given node"""
    all_components = digraph.strongly_connected_components()
    idx: cython.int
    for idx in range(len(all_components)):
        if node_index in all_components[idx]:
            return all_components[idx]
    raise RuntimeError("node_index not found in strongly_connected_components")


def generator_reach_calculate_reachable_costs(
    digraph: RustworkXGraph,
    world_graph: WorldGraph,
    state: State,
) -> Mapping[int, float]:
    """Calculate the reachable costs for GeneratorReach."""
    resources: ResourceCollection = state.resources
    nodes: list[WorldGraphNode] = world_graph.nodes

    is_collected: vector[cython.int] = vector[cython.int]()
    is_collected.resize(len(nodes), 2)

    def weight(data: tuple[int, int, GraphData]) -> int:
        node_index: cython.int = data[1]
        result: cython.int = is_collected[node_index]
        if result == 2:
            result = not nodes[node_index].resource_gain_bitmask.is_subset_of(resources.resource_bitmask)
            is_collected[node_index] = result

        return result

    return digraph.shortest_paths_dijkstra(
        state.node.node_index,
        weight=weight,
    )


def state_collect_resource_node(
    node: WorldGraphNode, resources: ResourceCollection, health: cython.float
) -> tuple[ResourceCollection, list[ResourceInfo]]:
    """
    Creates the new ResourceCollection and finds the modified resources, for State.collect_resource_node
    """
    modified_resources: list[ResourceInfo] = []
    new_resources = resources.duplicate()

    if not (not node.has_all_resources(resources) and node.requirement_to_collect.satisfied(resources, health)):
        raise ValueError(f"Trying to collect an uncollectable node'{node}'")

    for resource, quantity in node.resource_gain_on_collect(resources):
        new_resources.add_resource(resource, quantity)
        modified_resources.append(resource)

    return new_resources, modified_resources
