from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.requirements.base import Requirement

if TYPE_CHECKING:
    from collections.abc import Iterator

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

    def simplify(self, keep_comments: bool = False) -> Requirement:
        return self

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RequirementTemplate) and self.template_name == other.template_name

    def __hash__(self) -> int:
        return hash(self.template_name)

    def __str__(self) -> str:
        return self.template_name

    def iterate_resource_requirements(self, database: ResourceDatabase) -> Iterator[ResourceRequirement]:
        yield from self.template_requirement(database).iterate_resource_requirements(database)
