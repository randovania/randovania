from __future__ import annotations

import logging
import typing
from functools import lru_cache

from randovania.game_description.requirements.requirement_list import RequirementList

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement
    from randovania.game_description.resources.resource_info import ResourceInfo


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
            if not any(other.is_proper_subset_of(requirement) for other in input_set)
        )

    def __deepcopy__(self, memodict: dict) -> RequirementSet:
        return self

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RequirementSet) and self.alternatives == other.alternatives

    def __hash__(self) -> int:
        if self._cached_hash is None:
            self._cached_hash = hash(self.alternatives)
        return self._cached_hash

    def __repr__(self) -> str:
        return repr(self.alternatives)

    def pretty_print(self, indent: str = "", print_function: typing.Callable[[str], None] = logging.info) -> None:
        to_print = []
        if self == RequirementSet.impossible():
            to_print.append("Impossible")
        elif self == RequirementSet.trivial():
            to_print.append("Trivial")
        else:
            to_print.extend(str(alternative) for alternative in self.alternatives)
        for line in sorted(to_print):
            print_function(indent + line)

    @property
    def as_str(self) -> str:
        buffer: list[str] = []
        self.pretty_print(print_function=buffer.append)
        if len(buffer) > 1:
            return " or ".join(f"({it})" for it in buffer)
        else:
            return buffer[0]

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

    def satisfied(self, context: NodeContext, current_energy: int) -> bool:
        """
        Checks if at least one alternative is satisfied with the given resources.
        In particular, an empty RequirementSet is *never* considered satisfied.
        :param context:
        :param current_energy:
        :return:
        """
        for requirement_list in self.alternatives:
            if requirement_list.satisfied(context, current_energy):
                return True
        return False

    def union(self, other: RequirementSet) -> RequirementSet:
        """Create a new RequirementSet that is only satisfied when both are satisfied"""
        return RequirementSet(a.union(b) for a in self.alternatives for b in other.alternatives)

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

    def patch_requirements(self, context: NodeContext) -> RequirementSet:
        from randovania.game_description.requirements.requirement_and import RequirementAnd
        from randovania.game_description.requirements.requirement_or import RequirementOr

        return RequirementOr(
            RequirementAnd(individual.patch_requirements(1, context) for individual in alternative.values())
            for alternative in self.alternatives
        ).as_set(context)
