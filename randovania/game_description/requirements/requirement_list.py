from __future__ import annotations

import itertools
import typing
from typing import Iterable, Iterator

from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection, ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType

if typing.TYPE_CHECKING:
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement


def _key_hash(req: ResourceRequirement):
    return req.resource.resource_index, req.amount, req.negate


class RequirementList:
    __slots__ = ("_bitmask", "_items", "_extra", "_cached_hash")
    _bitmask: int
    _items: dict[tuple[int, int, bool], ResourceRequirement]
    _extra: list[ResourceRequirement]
    _cached_hash: int | None

    def __deepcopy__(self, memodict):
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

    def __eq__(self, other):
        return isinstance(other, RequirementList) and self._items == other._items

    @property
    def as_stable_sort_tuple(self):
        return len(self._items), sorted(self._items.keys())

    def __hash__(self) -> int:
        if self._cached_hash is None:
            self._cached_hash = hash(tuple(self._items.keys()))
        return self._cached_hash

    def __repr__(self):
        return repr(self._items)

    def __str__(self) -> str:
        if self._items:
            return ", ".join(sorted(str(item) for item in self._items.values()))
        else:
            return "Trivial"

    def damage(self, current_resources: ResourceCollection, database: ResourceDatabase):
        return sum(requirement.damage(current_resources, database) for requirement in self._extra)

    def satisfied(self, current_resources: ResourceCollection, current_energy: int, database: ResourceDatabase) -> bool:
        """
        A list is considered satisfied if each IndividualRequirement that belongs to it is satisfied.
        In particular, an empty RequirementList is considered satisfied.
        :param current_resources:
        :param current_energy:
        :param database:
        :return:
        """
        if self._bitmask & current_resources.resource_bitmask != self._bitmask:
            return False

        energy = current_energy
        for requirement in self._extra:
            if requirement.satisfied(current_resources, energy, database):
                if requirement.resource.resource_type == ResourceType.DAMAGE:
                    energy -= requirement.damage(current_resources, database)
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

    def is_subset_of(self, requirement: RequirementList) -> bool:
        if len(self._items) >= len(requirement._items):
            return False
        return all(key in requirement._items for key in self._items.keys())


SatisfiableRequirements = frozenset[RequirementList]
