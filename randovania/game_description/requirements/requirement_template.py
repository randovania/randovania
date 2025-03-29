from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.requirements.base import Requirement

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.requirements.requirement_set import RequirementSet
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement
    from randovania.game_description.resources.resource_database import ResourceDatabase


class RequirementTemplate(Requirement):
    __slots__ = ("template_name",)
    template_name: str

    def __init__(self, template_name: str):
        self.template_name = template_name

    def __copy__(self) -> RequirementTemplate:
        return RequirementTemplate(self.template_name)

    def __reduce__(self) -> tuple[type[RequirementTemplate], tuple[str]]:
        return RequirementTemplate, (self.template_name,)

    def template_requirement(self, database: ResourceDatabase) -> Requirement:
        return database.requirement_template[self.template_name].requirement

    def damage(self, context: NodeContext) -> int:
        return self.template_requirement(context.database).damage(context)

    def satisfied(self, context: NodeContext, current_energy: int) -> bool:
        return self.template_requirement(context.database).satisfied(context, current_energy)

    def patch_requirements(self, damage_multiplier: float, context: NodeContext) -> Requirement:
        return self.template_requirement(context.database).patch_requirements(damage_multiplier, context)

    def simplify(self, keep_comments: bool = False) -> Requirement:
        return self

    def isolate_damage_requirements(self, context: NodeContext) -> Requirement:
        return self.template_requirement(context.database).isolate_damage_requirements(context)

    def as_set(self, context: NodeContext) -> RequirementSet:
        return self.template_requirement(context.database).as_set(context)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RequirementTemplate) and self.template_name == other.template_name

    def __hash__(self) -> int:
        return hash(self.template_name)

    def __str__(self) -> str:
        return self.template_name

    def iterate_resource_requirements(self, context: NodeContext) -> Iterator[ResourceRequirement]:
        yield from self.template_requirement(context.database).iterate_resource_requirements(context)
