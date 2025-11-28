from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from randovania._native import GraphRequirementList, GraphRequirementSet

if TYPE_CHECKING:
    from collections.abc import Sequence

    from randovania.game_description.requirements.resource_requirement import ResourceRequirement


def create_requirement_list(resource_requirements: Sequence[ResourceRequirement]) -> GraphRequirementList:
    result = GraphRequirementList()
    for it in resource_requirements:
        result.add_resource(it.resource, it.amount, it.negate)
    return result


def create_requirement_set(
    entries: Sequence[GraphRequirementList], *, copy_entries: bool = False
) -> GraphRequirementSet:
    result = GraphRequirementSet()
    if copy_entries:
        result.extend_alternatives(copy.copy(it) for it in entries)
    else:
        result.extend_alternatives(entries)
    return result


__all__ = ["GraphRequirementList", "GraphRequirementSet", "create_requirement_list", "create_requirement_set"]
