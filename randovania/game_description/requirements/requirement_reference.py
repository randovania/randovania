from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_set import RequirementSet

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement


class RequirementReference(Requirement):
    __slots__ = ("references",)
    references: tuple[NodeIdentifier, ...]

    def __init__(self, references: tuple[NodeIdentifier, ...]):
        self.references = references

    def __copy__(self) -> RequirementReference:
        return RequirementReference(self.references)

    def __reduce__(self) -> tuple[type[RequirementReference], tuple[tuple[NodeIdentifier, ...]]]:
        return RequirementReference, (self.references,)

    def referenced_requirements(self, context: NodeContext) -> Iterator[Requirement]:
        nodes = [context.node_provider.node_by_identifier(it) for it in self.references]
        # TODO: gotta avoid calling potential_nodes_from for just one node
        requirements = [dict(context.node_provider.potential_nodes_from(node, context)) for node in nodes]
        for before, after in zip(nodes[:-1], nodes[1:], strict=True):
            yield requirements[before][after]

    def damage(self, context: NodeContext) -> int:
        dmg = 0
        for requirement in self.referenced_requirements(context):
            dmg += requirement.damage(context)
        return dmg

    def satisfied(self, context: NodeContext, current_energy: int) -> bool:
        for requirement in self.referenced_requirements(context):
            if not requirement.satisfied(context, current_energy):
                return False
        return True

    def patch_requirements(self, damage_multiplier: float, context: NodeContext) -> Requirement:
        return self

    def simplify(self, keep_comments: bool = False) -> Requirement:
        return self

    def as_set(self, context: NodeContext) -> RequirementSet:
        result = RequirementSet.trivial()
        for item in self.referenced_requirements(context):
            result = result.union(item.as_set(context))
        return result

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RequirementReference) and self.references == other.references

    def __hash__(self) -> int:
        return hash(self.references)

    def iterate_resource_requirements(self, context: NodeContext) -> Iterator[ResourceRequirement]:
        yield from []
