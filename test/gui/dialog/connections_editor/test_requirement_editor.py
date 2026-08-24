from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6.QtWidgets import QWidget

from randovania.game_description.resources.resource_type import ResourceType
from randovania.gui.dialog.connections_editor import requirement_tree
from randovania.gui.dialog.connections_editor.editor import (
    ArrayEditor,
    CountedResourceEditor,
    Editor,
    NodeEditor,
    SimpleResourceEditor,
    TemplateEditor,
    TrickResourceEditor,
)
from randovania.gui.dialog.connections_editor.model import ROLE

if TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region import Region


@pytest.fixture
def parent(skip_qtbot):
    widget = QWidget()
    skip_qtbot.addWidget(widget)
    return widget


@pytest.fixture
def array_editor(parent, echoes_resource_database):
    return ArrayEditor(echoes_resource_database, parent)


@pytest.fixture
def item_editor(parent, echoes_resource_database):
    return CountedResourceEditor(echoes_resource_database, parent, "Item", ResourceType.ITEM)


@pytest.fixture
def event_editor(parent, echoes_resource_database):
    return SimpleResourceEditor(echoes_resource_database, parent, "Event", ResourceType.EVENT)


@pytest.fixture
def trick_editor(parent, echoes_resource_database):
    return TrickResourceEditor(echoes_resource_database, parent)


@pytest.fixture
def damage_editor(parent, echoes_resource_database):
    return CountedResourceEditor(echoes_resource_database, parent, "Damage", ResourceType.DAMAGE)


@pytest.fixture
def version_editor(parent, echoes_resource_database):
    return SimpleResourceEditor(echoes_resource_database, parent, "Version", ResourceType.VERSION)


@pytest.fixture
def misc_editor(parent, echoes_resource_database):
    return SimpleResourceEditor(echoes_resource_database, parent, "Misc", ResourceType.MISC)


@pytest.fixture
def template_editor(parent, echoes_resource_database):
    return TemplateEditor(echoes_resource_database, parent)


@pytest.fixture
def node_editor(parent, echoes_game_description):
    return NodeEditor(echoes_game_description.resource_database, parent, echoes_game_description.region_list)


EDITOR_FIXTURES = [
    "array_editor",
    "item_editor",
    "event_editor",
    "trick_editor",
    "damage_editor",
    "version_editor",
    "misc_editor",
    "template_editor",
    "node_editor",
]


@pytest.mark.parametrize("editor_fixture_name", EDITOR_FIXTURES)
def test_editor_populate_and_return_requirement_round_trip(request, editor_fixture_name, echoes_game_description):
    editor: Editor = request.getfixturevalue(editor_fixture_name)

    original = requirement_tree.default_from_type(
        editor.type_of(), echoes_game_description.resource_database, echoes_game_description.region_list
    )

    editor.populate(original)
    result = editor.requirement()

    assert result == original


@pytest.mark.parametrize("target_idx", [1, 3, 4, 7, 8])
def test_node_editor_region_change_propogates(node_editor, echoes_game_description, target_idx):
    requirement = requirement_tree.default_from_type(
        node_editor.type(), echoes_game_description.resource_database, echoes_game_description.region_list
    )
    node_editor.populate(requirement)

    target_region: Region = echoes_game_description.region_list.regions[target_idx]
    target_area: Area = next(iter(target_region.areas))
    target_node: Node = next(iter(target_area.nodes))

    node_editor._combo_region.setCurrentIndex(target_idx)
    assert node_editor._combo_node.currentData(ROLE) == target_node
