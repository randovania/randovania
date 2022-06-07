from __future__ import annotations

import typing
from typing import FrozenSet, Optional, Iterable, Iterator

from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection, ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType

if typing.TYPE_CHECKING:
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement


class RequirementList:
    items: FrozenSet[ResourceRequirement]
    _cached_hash: Optional[int] = None

    def __deepcopy__(self, memodict):
        return self

    def __init__(self, items: Iterable[ResourceRequirement]):
        self.items = frozenset(items)

    def __eq__(self, other):
        return isinstance(other, RequirementList) and self.items == other.items

    @property
    def as_stable_sort_tuple(self):
        return len(self.items), sorted(self.items)

    def __hash__(self) -> int:
        if self._cached_hash is None:
            self._cached_hash = hash(self.items)
        return self._cached_hash

    def __repr__(self):
        return repr(self.items)

    def __str__(self) -> str:
        if self.items:
            return ", ".join(sorted(map(str, self.items)))
        else:
            return "Trivial"

    def damage(self, current_resources: ResourceCollection, database: ResourceDatabase):
        return sum(requirement.damage(current_resources, database) for requirement in self.values())

    def satisfied(self, current_resources: ResourceCollection, current_energy: int, database: ResourceDatabase) -> bool:
        """
        A list is considered satisfied if each IndividualRequirement that belongs to it is satisfied.
        In particular, an empty RequirementList is considered satisfied.
        :param current_resources:
        :param current_energy:
        :param database:
        :return:
        """

        energy = current_energy
        for requirement in self.values():
            if requirement.satisfied(current_resources, energy, database):
                if requirement.resource.resource_type == ResourceType.DAMAGE:
                    energy -= requirement.damage(current_resources, database)
            else:
                return False
        return True

    def get(self, resource: ResourceInfo) -> Optional[ResourceRequirement]:
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
        for individual in self.values():
            if individual.negate:
                yield individual.resource

    def values(self) -> FrozenSet[ResourceRequirement]:
        return self.items

    def union(self, other: RequirementList) -> RequirementList:
        return RequirementList(self.items | other.items)


SatisfiableRequirements = FrozenSet[RequirementList]
