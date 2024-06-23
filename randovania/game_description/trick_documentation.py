from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.area import Area
    from randovania.game_description.requirements.base import Requirement


class TrickUsageState(enum.IntEnum):
    UNDOCUMENTED = enum.auto()
    SKIPPED = enum.auto()
    DOCUMENTED = enum.auto()


EXCLUSION_KEYWORDS = (
    "TODO",
    "FIXME",
)


def _find_tricks_usage_documentation(requirement: Requirement) -> Iterator[tuple[str, TrickUsageState]]:
    from randovania.layout.base.trick_level import LayoutTrickLevel

    if not isinstance(requirement, RequirementArrayBase):
        return

    documentation_state = TrickUsageState.SKIPPED

    trick_resources = []
    for it in requirement.items:
        if isinstance(it, RequirementArrayBase):
            yield from _find_tricks_usage_documentation(it)

        elif isinstance(it, ResourceRequirement) and it.resource.resource_type == ResourceType.TRICK:
            assert isinstance(it.resource, TrickResourceInfo)
            trick_resources.append(it)
            if it.amount > it.resource.require_documentation_above:
                documentation_state = TrickUsageState.DOCUMENTED

    undocumented = requirement.comment is None or any(
        keyword.casefold() in requirement.comment.casefold() for keyword in EXCLUSION_KEYWORDS
    )
    if documentation_state == TrickUsageState.DOCUMENTED and undocumented:
        documentation_state = TrickUsageState.UNDOCUMENTED

    if trick_resources:
        yield (
            ", ".join(
                sorted(
                    f"{req.resource.long_name} ({LayoutTrickLevel.from_number(req.amount).long_name})"
                    for req in trick_resources
                )
            ),
            documentation_state,
        )


def _flat_trick_usage(requirement: Requirement) -> dict[str, TrickUsageState]:
    doc: dict[str, TrickUsageState] = {}
    for usage, documented in sorted(set(_find_tricks_usage_documentation(requirement))):
        doc[usage] = min(documented, doc.get(usage, TrickUsageState.DOCUMENTED))
    return doc


def get_area_connection_docs(area: Area) -> dict[str, dict[str, dict[str, TrickUsageState]]]:
    paths: dict[str, dict[str, dict[str, TrickUsageState]]] = {}
    for source, connections in area.connections.items():
        if source.is_derived_node:
            continue
        paths[source.name] = {}
        for target, requirement in connections.items():
            if target.is_derived_node:
                continue
            trick_documentation = _flat_trick_usage(requirement)
            if trick_documentation:
                paths[source.name][target.name] = trick_documentation
    return paths
