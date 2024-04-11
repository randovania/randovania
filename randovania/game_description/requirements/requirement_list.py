from __future__ import annotations

import itertools
import typing

from randovania.game_description.resources.resource_type import ResourceType

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement
    from randovania.game_description.resources.resource_info import ResourceInfo

_ItemKey = tuple[int, int, bool]


def _key_hash(req: ResourceRequirement) -> _ItemKey:
    return req.resource.resource_index, req.amount, req.negate


class RequirementList:
    __slots__ = ("_bitmask", "_items", "_extra", "_cached_hash")
    _bitmask: int
    _items: dict[_ItemKey, ResourceRequirement]
    _extra: list[ResourceRequirement]
    _cached_hash: int | None

    def __copy__(self) -> typing.Self:
        return self

    def __deepcopy__(self, memodict: dict) -> RequirementList:
        return self

    def __init__(self, items: Iterable[ResourceRequirement]):
        self._items = {}
        self._extra = []
        self._bitmask = 0
        self._cached_hash = None

        for it in items:
            self._items[_key_hash(it)] = it
            if it.amount == 1 and not it.negate and not it.is_damage:
                self._bitmask |= 1 << it.resource.resource_index
            else:
                self._extra.append(it)

    def __reduce__(self) -> tuple[type[RequirementList], tuple[ResourceRequirement, ...]]:
        return RequirementList, tuple(self._items.values())

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RequirementList) and self._items == other._items

    @property
    def as_stable_sort_tuple(self) -> tuple[int, list[_ItemKey]]:
        return len(self._items), sorted(self._items.keys())

    def __hash__(self) -> int:
        if self._cached_hash is None:
            self._cached_hash = hash(tuple(self._items.keys()))
        return self._cached_hash

    def __repr__(self) -> str:
        return repr(list(self._items.values()))

    def __str__(self) -> str:
        if self._items:
            return ", ".join(sorted(str(item) for item in self._items.values()))
        else:
            return "Trivial"

    def damage(self, context: NodeContext) -> int:
        return sum(requirement.damage(context) for requirement in self._extra)

    def satisfied(self, context: NodeContext, current_energy: int) -> bool:
        """
        A list is considered satisfied if each IndividualRequirement that belongs to it is satisfied.
        In particular, an empty RequirementList is considered satisfied.
        :param context:
        :param current_energy:
        :return:
        """
        if self._bitmask & context.current_resources.resource_bitmask != self._bitmask:
            return False

        energy = current_energy
        for requirement in self._extra:
            if requirement.satisfied(context, energy):
                if requirement.resource.resource_type == ResourceType.DAMAGE:
                    energy -= requirement.damage(context)
            else:
                return False
        return True

    def get(self, resource: ResourceInfo) -> ResourceRequirement | None:
        """
        Gets an IndividualRequirement that uses the given resource
        :param resource:
        :return:
        """
        for item in self.values():
            if item.resource == resource:
                return item
        return None

    @property
    def dangerous_resources(self) -> Iterator[ResourceInfo]:
        """
        Return an iterator of all SimpleResourceInfo in this list that have the negate flag
        :return:
        """
        for individual in self._extra:
            if individual.negate:
                yield individual.resource

    def values(self) -> Iterator[ResourceRequirement]:
        yield from self._items.values()

    def union(self, other: RequirementList) -> RequirementList:
        return RequirementList(itertools.chain(self.values(), other.values()))

    def is_proper_subset_of(self, other: RequirementList) -> bool:
        """
        Returns True when every requirement in self is also present in other, either directly or with a bigger amount.
        However, returns False if equal.

        """
        if len(self._items) > len(other._items):
            return False

        if self._items == other._items:
            return False

        return all(
            key in other._items or any(req.is_obsoleted_by(other_req) for other_req in other._items.values())
            for key, req in self._items.items()
        )


SatisfiableRequirements = frozenset[RequirementList]
