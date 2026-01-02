from __future__ import annotations

import typing
from functools import lru_cache

if typing.TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement


class Requirement:
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
