from __future__ import annotations

import typing
from functools import lru_cache

from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection

if typing.TYPE_CHECKING:
    from randovania.game_description.requirements.requirement_set import RequirementSet
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement

MAX_DAMAGE = 9999999


class Requirement:
    def damage(self, current_resources: ResourceCollection, database: ResourceDatabase) -> int:
        raise NotImplementedError()

    def satisfied(self, current_resources: ResourceCollection, current_energy: int, database: ResourceDatabase) -> bool:
        raise NotImplementedError()

    def patch_requirements(self, static_resources: ResourceCollection, damage_multiplier: float,
                           database: ResourceDatabase) -> Requirement:
        """
        Creates a new Requirement that does not contain reference to resources in static_resources.
        For those that contains a reference, they're replaced with Trivial when satisfied and Impossible otherwise.
        :param static_resources:
        :param damage_multiplier: All damage requirements have their value multiplied by this.
        :param database:
        """
        raise NotImplementedError()

    def simplify(self, *, keep_comments: bool = False) -> Requirement:
        """
        Creates a new Requirement without some redundant complexities, like:
        - RequirementAnd/RequirementOr of exactly one item
        - RequirementAnd/RequirementOr of others of the same type.
        - RequirementAnd with impossible among the items
        - RequirementOr with trivial among the items
        :return:
        """
        raise NotImplementedError()

    def as_set(self, database: ResourceDatabase) -> RequirementSet:
        raise NotImplementedError()

    @classmethod
    @lru_cache
    def trivial(cls) -> Requirement:
        # empty RequirementAnd.satisfied is True
        from randovania.game_description.requirements.requirement_and import RequirementAnd
        return RequirementAnd([])

    @classmethod
    @lru_cache
    def impossible(cls) -> Requirement:
        # empty RequirementOr.satisfied is False
        from randovania.game_description.requirements.requirement_or import RequirementOr
        return RequirementOr([])

    def __lt__(self, other: Requirement):
        return str(self) < str(other)

    def iterate_resource_requirements(self, database: ResourceDatabase) -> typing.Iterator[ResourceRequirement]:
        raise NotImplementedError()
