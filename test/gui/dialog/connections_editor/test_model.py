from __future__ import annotations

import pytest

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.gui.dialog.connections_editor.model import ROLE, RequirementModel
from randovania.gui.dialog.connections_editor.path import Path


def item(name: str, db: ResourceDatabase):
    return ResourceRequirement.with_data(db, ResourceType.ITEM, name, 1, False)


@pytest.fixture
def model() -> RequirementModel:
    return RequirementModel()


@pytest.fixture
def requirement(echoes_resource_database):
    return RequirementOr(
        [
            item("ScrewAttack", echoes_resource_database),
            RequirementAnd([item("Dark", echoes_resource_database), item("Light", echoes_resource_database)], "Beams"),
            RequirementTemplate("Has Suit"),
            NodeRequirement(NodeIdentifier("Sanctuary Fortress", "Grand Abyss", "Door to Vault")),
            RequirementAnd(
                [
                    item("Charge", echoes_resource_database),
                    RequirementOr(
                        [
                            item("Supers", echoes_resource_database),
                            item("Darkburst", echoes_resource_database),
                            item("Sunburst", echoes_resource_database),
                            item("SonicBoom", echoes_resource_database),
                        ]
                    ),
                ]
            ),
        ]
    )


def test_build_no_changes(model, requirement):
    model.build_tree(requirement)
    assert model.build_requirement() == requirement


def test_path_from_index_discards_root(model, requirement):
    model.build_tree(requirement)

    root_index = model.invisibleRootItem().index()
    or_index = model.index(0, 0, root_index)
    template_index = model.index(2, 0, or_index)

    assert model.path_from_index(template_index) == Path((2,))


def test_index_from_path_adds_root(model, requirement, echoes_resource_database):
    model.build_tree(requirement)
    path = Path((1, 0))
    assert model.index_from_path(path).data(ROLE) == item("Dark", echoes_resource_database)


@pytest.mark.parametrize(("path", "expected"), [(Path((1, 1)), 1), (Path((3,)), 4), (Path((4, 1, 0)), 3)])
def test_sibling_count_is_last_index(model, requirement, path, expected):
    model.build_tree(requirement)
    assert model.sibling_count(path) == expected
