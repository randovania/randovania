from __future__ import annotations

import pytest

from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.resources.resource_type import ResourceType
from randovania.gui.dialog.connections_editor import requirement_tree
from randovania.gui.dialog.connections_editor.connections_editor import ConnectionsEditor
from randovania.gui.dialog.connections_editor.path import Path


@pytest.fixture
def connections_editor(skip_qtbot, echoes_game_description, echoes_varied_requirement):
    # parent=None sidesteps a python garbage collection issue
    # A locally-defined parent goes out of scope when the fixture returns
    # This causes the editor and its children to be deleted
    editor = ConnectionsEditor(
        None,  # type: ignore[arg-type]
        echoes_game_description.resource_database,
        echoes_game_description.region_list,
        echoes_varied_requirement,
    )
    skip_qtbot.addWidget(editor)
    return editor


def test_connections_editor_build_no_changes(skip_qtbot, connections_editor, echoes_varied_requirement):
    assert connections_editor.final_requirement == echoes_varied_requirement


@pytest.mark.parametrize("type", [ResourceType.ITEM, ResourceType.TRICK, RequirementTemplate, NodeRequirement])
def test_connections_editor_build_change_root(skip_qtbot, connections_editor, type, echoes_game_description):
    expected = requirement_tree.change_to_type(
        connections_editor.final_requirement,
        type,
        echoes_game_description.resource_database,
        echoes_game_description.region_list,
    )

    connections_editor._view.restore_selection(Path())  # Select root
    connections_editor._controller._on_editor_field_changed(expected)
    assert connections_editor.final_requirement == expected
