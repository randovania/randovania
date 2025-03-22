from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.requirements.base import MAX_DAMAGE, Requirement
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.node_resource_info import NodeResourceInfo

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.db.node_identifier import NodeIdentifier


class NodeRequirement(Requirement):
    __slots__ = ("node_identifier",)
    node_identifier: NodeIdentifier

    def __copy__(self) -> NodeRequirement:
        return NodeRequirement(self.node_identifier)

    def __reduce__(self) -> tuple[type[NodeRequirement], tuple[NodeIdentifier]]:
        return type(self), (self.node_identifier,)

    def __init__(self, node_identifier: NodeIdentifier):
        self.node_identifier = node_identifier

    def __repr__(self) -> str:
        return f"Req {self.node_identifier}"

    @property
    def is_damage(self) -> bool:
        return False

    def damage(self, context: NodeContext) -> int:
        if self.satisfied(context, MAX_DAMAGE):
            return 0
        else:
            return MAX_DAMAGE

    def satisfied(self, context: NodeContext, current_energy: int) -> bool:
        """Checks if a given resource collection satisfies this requirement"""
        return context.current_resources[NodeResourceInfo.from_identifier(self.node_identifier, context)] >= 1

    def simplify(self, keep_comments: bool = False) -> Requirement:
        return self

    def isolate_damage_requirements(self, context: NodeContext) -> Requirement:
        return Requirement.trivial() if self.satisfied(context, 0) else Requirement.impossible()

    @property
    def pretty_text(self) -> str:
        return str(self.node_identifier)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NodeRequirement):
            return False
        return self.node_identifier == other.node_identifier

    def __lt__(self, other: Requirement) -> bool:
        assert isinstance(other, NodeRequirement)
        return self.node_identifier < other.node_identifier

    def __hash__(self) -> int:
        return hash(self.node_identifier)

    def as_resource_requirement(self, context: NodeContext) -> ResourceRequirement:
        return ResourceRequirement.simple(NodeResourceInfo.from_identifier(self.node_identifier, context))

    def patch_requirements(self, damage_multiplier: float, context: NodeContext) -> Requirement:
        return self.as_resource_requirement(context)

    def as_set(self, context: NodeContext) -> RequirementSet:
        return RequirementSet([RequirementList([self.as_resource_requirement(context)])])

    def iterate_resource_requirements(self, context: NodeContext) -> Iterator[ResourceRequirement]:
        yield self.as_resource_requirement(context)
