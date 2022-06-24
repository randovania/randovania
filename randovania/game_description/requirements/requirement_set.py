from __future__ import annotations

import logging
import typing
from functools import lru_cache
from typing import Iterable, Iterator

from randovania.game_description.requirements.requirement_list import RequirementList

if typing.TYPE_CHECKING:
    from randovania.game_description.resources.resource_info import ResourceCollection, ResourceInfo
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement


class RequirementSet:
    """
    Represents multiple alternatives of satisfying a requirement.
    For example, going from A to B may be possible by having Grapple+Space Jump or Screw Attack.
    """
    alternatives: frozenset[RequirementList]
    _cached_hash: int | None = None

    def __init__(self, alternatives: Iterable[RequirementList]):
        """
        Constructs a RequirementSet from given iterator of RequirementList.
        Redundant alternatives (Bombs or Bombs + Space Jump) are automatically removed.
        :param alternatives:
        """
        input_set = frozenset(alternatives)
        self.alternatives = frozenset(
            requirement
            for requirement in input_set
            if not any(other.is_subset_of(requirement) for other in input_set)
        )

    def __deepcopy__(self, memodict):
        return self

    def __eq__(self, other):
        return isinstance(
            other, RequirementSet) and self.alternatives == other.alternatives

    def __hash__(self) -> int:
        if self._cached_hash is None:
            self._cached_hash = hash(self.alternatives)
        return self._cached_hash

    def __repr__(self):
        return repr(self.alternatives)

    def pretty_print(self, indent="", print_function=logging.info):
        to_print = []
        if self == RequirementSet.impossible():
            to_print.append("Impossible")
        elif self == RequirementSet.trivial():
            to_print.append("Trivial")
        else:
            to_print.extend(
                str(alternative)
                for alternative in self.alternatives
            )
        for line in sorted(to_print):
            print_function(indent + line)

    @property
    def as_str(self):
        l = []
        self.pretty_print(print_function=l.append)
        if len(l) > 1:
            return " or ".join(f"({it})" for it in l)
        else:
            return l[0]

    @classmethod
    @lru_cache
    def trivial(cls) -> RequirementSet:
        # empty RequirementList.satisfied is True
        return cls([RequirementList([])])

    @classmethod
    @lru_cache
    def impossible(cls) -> RequirementSet:
        # No alternatives makes satisfied always return False
        return cls([])

    def satisfied(self, current_resources: ResourceCollection, current_energy: int, database: ResourceDatabase) -> bool:
        """
        Checks if at least one alternative is satisfied with the given resources.
        In particular, an empty RequirementSet is *never* considered satisfied.
        :param current_resources:
        :param current_energy:
        :param database:
        :return:
        """
        for requirement_list in self.alternatives:
            if requirement_list.satisfied(current_resources, current_energy, database):
                return True
        return False

    def union(self, other: RequirementSet) -> RequirementSet:
        """Create a new RequirementSet that is only satisfied when both are satisfied"""
        return RequirementSet(
            a.union(b)
            for a in self.alternatives
            for b in other.alternatives)

    def expand_alternatives(self, other: RequirementSet) -> RequirementSet:
        """Create a new RequirementSet that is satisfied when either are satisfied."""
        return RequirementSet(self.alternatives | other.alternatives)

    @property
    def dangerous_resources(self) -> Iterator[ResourceInfo]:
        """
        Return an iterator of all SimpleResourceInfo in all alternatives that have the negate flag
        :return:
        """
        for alternative in self.alternatives:
            yield from alternative.dangerous_resources

    @property
    def all_individual(self) -> Iterator[ResourceRequirement]:
        """
        Iterates over all individual requirements involved in this set
        :return:
        """
        for alternative in self.alternatives:
            yield from alternative.values()

    def patch_requirements(self, resources: ResourceCollection, database: ResourceDatabase) -> RequirementSet:
        from randovania.game_description.requirements.requirement_and import RequirementAnd
        from randovania.game_description.requirements.requirement_or import RequirementOr
        return RequirementOr(
            RequirementAnd(
                individual.patch_requirements(resources, 1, database)
                for individual in alternative.values()
            )
            for alternative in self.alternatives
        ).as_set(database)
