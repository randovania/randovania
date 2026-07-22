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
from randovania.gui.dialog.connections_editor import requirement_tree
from randovania.gui.dialog.connections_editor.path import Path

TUPLE = (0, 2, 1)


@pytest.mark.parametrize(
    ("items", "idx", "value", "expected"),
    [(TUPLE, 0, 3, (3, *TUPLE)), (TUPLE, 1, 3, (0, 3, 2, 1)), (TUPLE, 2, 3, (0, 2, 3, 1)), (TUPLE, 3, 3, (*TUPLE, 3))],
)
def test_tuple_insert_inserts(items, idx, value, expected):
    assert requirement_tree.tuple_insert(items, idx, value) == expected


@pytest.mark.parametrize(
    ("items", "idx", "value", "expected"),
    [(TUPLE, 0, 3, (3, 2, 1)), (TUPLE, 1, 3, (0, 3, 1)), (TUPLE, 2, 3, (0, 2, 3))],
)
def test_tuple_replace_replaces(items, idx, value, expected):
    assert requirement_tree.tuple_replace(items, idx, value) == expected


@pytest.mark.parametrize(("items", "idx", "expected"), [(TUPLE, 0, (2, 1)), (TUPLE, 1, (0, 1)), (TUPLE, 2, (0, 2))])
def test_tuple_remove_removes(items, idx, expected):
    assert requirement_tree.tuple_remove(items, idx) == expected


def item(name: str, db: ResourceDatabase):
    return ResourceRequirement.with_data(db, ResourceType.ITEM, name, 1, False)


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
                        ],
                        "Combos",
                    ),
                ]
            ),
        ],
        "This is a varied Requirement tree!",
    )


@pytest.mark.parametrize(("path"), [Path((1, 1)), Path((4, 1, 2)), Path((0,))])
def test_insert_at_path_inserts(requirement, echoes_resource_database, path):
    inserted_item = item("MorphBall", echoes_resource_database)
    after_insert = requirement_tree.insert_at_path(requirement, path, inserted_item)
    assert requirement_tree._at_path(after_insert, path) == inserted_item


@pytest.mark.parametrize(("path"), [Path((1, 0)), Path((4, 1, 2)), Path((0,))])
def test_remove_at_path_removes(requirement, path):
    item_to_be_removed = requirement_tree._at_path(requirement, path)
    after_remove = requirement_tree.remove_at_path(requirement, path)
    assert requirement_tree._at_path(after_remove, path) != item_to_be_removed


@pytest.mark.parametrize(("path"), [Path((1, 1)), Path((4, 1, 2)), Path((0,))])
def test_replace_at_path_replaces(requirement, echoes_resource_database, path):
    item_to_replace_with = item("MorphBall", echoes_resource_database)
    after_replace = requirement_tree.replace_at_path(requirement, path, item_to_replace_with)
    assert requirement_tree._at_path(after_replace, path) == item_to_replace_with
