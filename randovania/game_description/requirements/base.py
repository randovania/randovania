from __future__ import annotations

import typing
from functools import lru_cache

if typing.TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.requirements.requirement_set import RequirementSet
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement

MAX_DAMAGE = 9999999


class Requirement:
    def damage(self, context: NodeContext) -> int:
        raise NotImplementedError

    def satisfied(self, context: NodeContext, current_energy: int) -> bool:
        raise NotImplementedError

    def patch_requirements(self, damage_multiplier: float, context: NodeContext) -> Requirement:
        """
        Creates a new Requirement that does not contain reference to resources in static_resources.
        For those that contains a reference, they're replaced with Trivial when satisfied and Impossible otherwise.
        :param damage_multiplier: All damage requirements have their value multiplied by this.
        :param context:
        """
        raise NotImplementedError

    def simplify(self, *, keep_comments: bool = False) -> Requirement:
        """
        Creates a new Requirement without some redundant complexities, like:
        - RequirementAnd/RequirementOr of exactly one item
        - RequirementAnd/RequirementOr of others of the same type.
        - RequirementAnd with impossible among the items
        - RequirementOr with trivial among the items
        :return:
        """
        raise NotImplementedError

    def isolate_damage_requirements(self, context: NodeContext) -> Requirement:
        """
        Strips away requirements not related to damage. For requirements that aren't damage related: unsatisfied
        requirements are replaced with impossible, satisfied ones are replaced with trivial.
        :param context:
        :return:
        """
        raise NotImplementedError

    def as_set(self, context: NodeContext) -> RequirementSet:
        raise NotImplementedError

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

    def __lt__(self, other: Requirement) -> bool:
        return str(self) < str(other)

    def iterate_resource_requirements(self, context: NodeContext) -> Iterator[ResourceRequirement]:
        raise NotImplementedError
