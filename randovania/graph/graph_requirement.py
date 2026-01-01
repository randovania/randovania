# distutils: language=c++
# cython: profile=False
# pyright: reportPossiblyUnboundVariable=false
# pyright: reportReturnType=false
# mypy: disable-error-code="return"

from __future__ import annotations

import copy
import functools
import logging
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

    # The package is named `Cython`, so in a case-sensitive system mypy fails to find cython with just `import cython`
    import Cython as cython

    from randovania.game_description.game_database_view import ResourceDatabaseView
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement
    from randovania.game_description.resources.resource_info import ResourceInfo
else:
    # However cython's compiler seems to expect the import to be this way, otherwise `cython.compiled` breaks
    import cython

# ruff: noqa: UP046
# ruff: noqa: UP037

if cython.compiled:
    if not typing.TYPE_CHECKING:
        from cython.cimports.libcpp.utility import pair
        from cython.cimports.libcpp.vector import vector
        from cython.cimports.randovania.game_description.resources.resource_collection import (
            ResourceCollection,  # noqa: TC002
        )
        from cython.cimports.randovania.lib.bitmask import Bitmask
else:
    from randovania.lib.bitmask import Bitmask
    from randovania.lib.cython_helper import Pair as pair
    from randovania.lib.cython_helper import PyImmutableRef, PyRef
    from randovania.lib.cython_helper import Vector as vector

    if typing.TYPE_CHECKING:
        from randovania.game_description.resources.resource_collection import ResourceCollection

        GraphRequirementListRef = PyImmutableRef["GraphRequirementList"]
        GraphRequirementSetRef = PyRef["GraphRequirementSet"]
    else:
        GraphRequirementListRef = PyImmutableRef
        GraphRequirementSetRef = PyRef


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

    def __init__(self, resource_db: ResourceDatabaseView | None) -> None:
        self._set_bitmask = Bitmask.create_native()
        self._negate_bitmask = Bitmask.create_native()
        self._other_resources = vector[pair[cython.size_t, cython.int]]()
        self._damage_resources = vector[pair[cython.size_t, cython.int]]()

        self._resource_db = resource_db
        self._frozen = False

    @staticmethod
    @cython.cfunc
    def from_components(
        resource_db: ResourceDatabaseView | None,
        set_bitmask: Bitmask,
        negate_bitmask: Bitmask,
        other_resources: vector[pair[cython.size_t, cython.int]],
        damage_resources: vector[pair[cython.size_t, cython.int]],
    ) -> GraphRequirementList:
        """Alternative constructor that accepts all components directly."""
        result: GraphRequirementList = GraphRequirementList.__new__(GraphRequirementList)
        result._set_bitmask = set_bitmask
        result._negate_bitmask = negate_bitmask
        if cython.compiled:
            result._other_resources = other_resources
            result._damage_resources = damage_resources
        else:
            result._other_resources = other_resources.copy_elements()
            result._damage_resources = damage_resources.copy_elements()
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
            result._other_resources = vector[pair[cython.size_t, cython.int]]()
            result._damage_resources = vector[pair[cython.size_t, cython.int]]()
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
            result ^= hash(tuple(sorted((entry.first, entry.second) for entry in self._other_resources)))
            result ^= hash(tuple(sorted((entry.first, entry.second) for entry in self._damage_resources))) * 37

        return hash(result)

    def _resource_mapping(self) -> dict[int, ResourceInfo]:
        if self._resource_db is None:
            return {}
        return self._resource_db.get_resource_mapping()

    @cython.ccall
    def is_frozen(self) -> cython.bint:
        """Returns True if `freeze` was previously called."""
        return self._frozen

    @cython.ccall
    def freeze(self) -> cython.void:
        """Prevents any further modifications to this GraphRequirementList. Copies won't be frozen."""
        self._frozen = True

    @cython.cfunc
    def _check_can_write(self) -> cython.void:
        if self._frozen:
            raise RuntimeError("Cannot modify a frozen GraphRequirementList")

    @cython.cfunc
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
        if cython.compiled:
            result._other_resources = self._other_resources
            result._damage_resources = self._damage_resources
        else:
            result._other_resources = self._other_resources.copy_elements()
            result._damage_resources = self._damage_resources.copy_elements()

        return result

    def __str__(self) -> str:
        mapping = self._resource_mapping()

        other_resources = {entry.first for entry in self._other_resources}

        parts = sorted(
            f"{mapping[resource_index].resource_type.non_negated_prefix}{mapping[resource_index]}"
            for resource_index in self._set_bitmask.get_set_bits()
            if resource_index not in other_resources
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

    @cython.cfunc
    @cython.exceptval(check=False)  # type: ignore[call-arg]
    def _find_other_idx(self, resource_index: cython.int) -> cython.int:
        """
        Searches self._other_resources for an entry with the given resource_index.
        Returns the index of the found entry, or -1 if not.
        """
        i: cython.int
        for i in range(self._other_resources.size()):
            if self._other_resources[i].first == resource_index:
                return i
        return -1

    @cython.cfunc
    @cython.exceptval(check=False)  # type: ignore[call-arg]
    def _find_damage_idx(self, resource_index: cython.int) -> cython.int:
        """
        Searches self._damage_resources for an entry with the given resource_index.
        Returns the index of the found entry, or -1 if not.
        """
        i: cython.int
        for i in range(self._damage_resources.size()):
            if self._damage_resources[i].first == resource_index:
                return i
        return -1

    @cython.ccall
    @cython.inline
    def num_requirements(self) -> cython.int:
        """Returns the total number of resource requirements in this list."""
        return self._set_bitmask.num_set_bits() + self._negate_bitmask.num_set_bits() + self._damage_resources.size()

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
    def all_resources(self, include_damage: cython.bint = True) -> set[ResourceInfo]:
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

        for entry in self._other_resources:
            if entry.first == resource_index:
                return entry.second, False

        if self._set_bitmask.is_set(resource_index):
            return 1, False

        if self._negate_bitmask.is_set(resource_index):
            return 1, True

        if include_damage:
            for entry in self._damage_resources:
                if entry.first == resource_index:
                    return entry.second, False

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

        idx: cython.int
        for entry in merge._other_resources:
            idx = self._find_other_idx(entry.first)
            if idx != -1:
                self._other_resources[idx].second = max(self._other_resources[idx].second, entry.second)
            else:
                self._other_resources.push_back(pair[cython.size_t, cython.int](entry))

        for entry in merge._damage_resources:
            idx = self._find_damage_idx(entry.first)
            if idx != -1:
                self._damage_resources[idx].second += entry.second
            else:
                self._damage_resources.push_back(pair[cython.size_t, cython.int](entry))

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

        result = GraphRequirementList.from_components(
            db,
            self._set_bitmask.copy(),
            self._negate_bitmask.copy(),
            self._other_resources,
            self._damage_resources,
        )

        # Copy and union bitmasks
        result._set_bitmask.union(right._set_bitmask)
        result._negate_bitmask.union(right._negate_bitmask)

        # Check if there's any conflict between set and negate requirements
        if result._set_bitmask.share_at_least_one_bit(result._negate_bitmask):
            return None

        idx: cython.int
        for entry in right._other_resources:
            idx = result._find_other_idx(entry.first)
            if idx != -1:
                result._other_resources[idx].second = max(result._other_resources[idx].second, entry.second)
            else:
                result._other_resources.push_back(pair[cython.size_t, cython.int](entry))

        for entry in right._damage_resources:
            idx = result._find_damage_idx(entry.first)
            if idx != -1:
                result._damage_resources[idx].second += entry.second
            else:
                result._damage_resources.push_back(pair[cython.size_t, cython.int](entry))

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
            idx: cython.int = self._find_other_idx(resource_index)
            if idx != -1:
                self._other_resources[idx].second = max(self._other_resources[idx].second, amount)
            else:
                self._other_resources.push_back(pair[cython.size_t, cython.int](resource_index, amount))

    @cython.ccall
    def add_damage(self, resource_index: cython.int, amount: cython.int) -> cython.void:
        self._check_can_write()
        idx: cython.int = self._find_damage_idx(resource_index)
        if idx != -1:
            self._damage_resources[idx].second += amount
        else:
            self._damage_resources.push_back(pair[cython.size_t, cython.int](resource_index, amount))

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
            return TRIVIAL_LIST

        result = GraphRequirementList.create_empty(self._resource_db)

        for entry in self._damage_resources:
            if resources.get_damage_reduction(entry.first) == 0:
                return GraphRequirementList.create_empty(self._resource_db)

            result._damage_resources.push_back(pair[cython.size_t, cython.int](entry))
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

        idx: cython.int
        # Check _other_resources - superset must have >= amounts for all resources in subset
        for subset_entry in subset_req._other_resources:
            idx = self._find_other_idx(subset_entry.first)
            if idx == -1 or self._other_resources[idx].second < subset_entry.second:
                return False

        # Check _damage_resources - superset must have >= amounts for all damage in subset
        for subset_entry in subset_req._damage_resources:
            idx = self._find_damage_idx(subset_entry.first)
            if idx == -1 or self._damage_resources[idx].second < subset_entry.second:
                return False

        # Remove duplicates
        return True

    @cython.cfunc
    def _simplify_handle_resource(
        self,
        resource_index: cython.size_t,
        amount: cython.int,
        negate: cython.bint,
        progressive_item_info: "None | tuple[Sequence[cython.size_t], int]",
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
        progressive_item_info: "None | tuple[Sequence[cython.size_t], int]",
    ) -> GraphRequirementList | None:
        """Used by resolver.py for `_simplify_additional_requirement_set`"""

        result = GraphRequirementList.create_empty(self._resource_db)
        something_set: cython.bint = False

        for resource_index in self._set_bitmask.get_set_bits():
            amount: cython.int = 1
            for self_entry in self._other_resources:
                if self_entry.first == resource_index:
                    amount = self_entry.second
                    break
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
                result._damage_resources.push_back(pair[cython.size_t, cython.int](entry))

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


TRIVIAL_LIST: GraphRequirementList = GraphRequirementList(None)
TRIVIAL_LIST.freeze()


@cython.final
@cython.cclass
class GraphRequirementSet:
    """
    Contains a list of GraphRequirement, but only one needs to be satisfied (OR).

    These two classes together represents a `Requirement` in disjunctive normal form.
    """

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
    def freeze(self) -> cython.void:
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

        if self is TRIVIAL_SET:
            return True

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
        return TRIVIAL_SET

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
        return IMPOSSIBLE_SET

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
                    return TRIVIAL_SET
                else:
                    result._alternatives.push_back(GraphRequirementListRef(isolated))

        return result

    def get_all_used_resources(self) -> tuple[set[int], set[int]]:
        """
        :return: A tuple with two sets of resource indices.
        The first is all resources used by any of the alternatives.
        The second is all resources used in at least one negate requirement.
        """
        set_resources: set[int] = set()
        resources_with_negate: set[int] = set()

        for ref in self._alternatives:
            alternative: GraphRequirementList = cython.cast(GraphRequirementList, ref.raw())

            for resource_index in alternative._set_bitmask.get_set_bits():
                set_resources.add(resource_index)

            for resource_index in alternative._negate_bitmask.get_set_bits():
                set_resources.add(resource_index)
                resources_with_negate.add(resource_index)

            for entry in alternative._damage_resources:
                set_resources.add(entry.first)

        return set_resources, resources_with_negate


TRIVIAL_SET = GraphRequirementSet()
TRIVIAL_SET.add_alternative(TRIVIAL_LIST)
TRIVIAL_SET.freeze()

# No alternatives makes satisfied always return False
IMPOSSIBLE_SET = GraphRequirementSet()
IMPOSSIBLE_SET.freeze()


def create_requirement_list(
    db: ResourceDatabaseView, resource_requirements: Sequence[ResourceRequirement]
) -> GraphRequirementList:
    result = GraphRequirementList(db)
    for it in resource_requirements:
        result.add_resource(it.resource, it.amount, it.negate)
    return result


def create_requirement_set(
    entries: Sequence[GraphRequirementList], *, copy_entries: bool = False
) -> GraphRequirementSet:
    result = GraphRequirementSet()
    if copy_entries:
        result.extend_alternatives(copy.copy(it) for it in entries)
    else:
        result.extend_alternatives(entries)
    return result
