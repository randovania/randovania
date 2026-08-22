from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from randovania.game_description.requirements.base import Requirement


@pytest.fixture
def make_and() -> Callable[[Iterable[Requirement], str | None], RequirementAnd]:
    def _make(items: Iterable[Requirement], comment: str | None = None):
        return RequirementAnd(items, comment)

    return _make


@pytest.fixture
def make_or() -> Callable[[Iterable[Requirement], str | None], RequirementAnd]:
    def _make(items: Iterable[Requirement], comment: str | None = None):
        return RequirementOr(items, comment)

    return _make


@pytest.fixture
def node() -> Callable[[str, str, str], NodeRequirement]:
    def _make(region: str, area: str, node: str):
        return NodeRequirement(NodeIdentifier(region, area, node))

    return _make


@pytest.fixture
def echoes_template(echoes_resource_database) -> Callable[[str], Requirement]:
    def _make(name: str):
        return RequirementTemplate(name).template_requirement(echoes_resource_database)

    return _make


@pytest.fixture
def echoes_resource_requirement(echoes_resource_database) -> Callable[[ResourceType, str], ResourceRequirement]:
    def _make(resource_type: ResourceType, name: str):
        return ResourceRequirement.with_data(echoes_resource_database, resource_type, name, 1, False)

    return _make


@pytest.fixture
def echoes_item(echoes_resource_requirement) -> Callable[[str], ResourceRequirement]:
    return lambda name: echoes_resource_requirement(ResourceType.ITEM, name)


@pytest.fixture
def echoes_event(echoes_resource_requirement) -> Callable[[str], ResourceRequirement]:
    return lambda name: echoes_resource_requirement(ResourceType.EVENT, name)


@pytest.fixture
def echoes_trick(echoes_resource_requirement) -> Callable[[str], ResourceRequirement]:
    return lambda name: echoes_resource_requirement(ResourceType.TRICK, name)


@pytest.fixture
def echoes_damage(echoes_resource_requirement) -> Callable[[str], ResourceRequirement]:
    return lambda name: echoes_resource_requirement(ResourceType.DAMAGE, name)


@pytest.fixture
def echoes_version(echoes_resource_requirement) -> Callable[[str], ResourceRequirement]:
    return lambda name: echoes_resource_requirement(ResourceType.VERSION, name)


@pytest.fixture
def echoes_misc(echoes_resource_requirement) -> Callable[[str], ResourceRequirement]:
    return lambda name: echoes_resource_requirement(ResourceType.MISC, name)


@pytest.fixture
def echoes_varied_requirement(
    make_and,
    make_or,
    echoes_template,
    echoes_item,
    echoes_event,
    echoes_trick,
    echoes_damage,
    echoes_version,
    echoes_misc,
    node,
) -> Requirement:
    return make_and(
        [
            make_or(
                [echoes_item("Power"), echoes_item("Dark"), echoes_item("Light"), echoes_item("Annihilator")], "Beams"
            ),
            echoes_event("Event1"),
            echoes_trick("Dash"),
            echoes_damage("Damage"),
            echoes_version("NTSC"),
            echoes_misc("SafeZone"),
            echoes_template("Has Suit"),
            node("Sanctuary Fortress", "Grand Abyss", "Door to Vault"),
        ],
        None,
    )
