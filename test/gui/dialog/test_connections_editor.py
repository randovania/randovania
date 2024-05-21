from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6 import QtWidgets

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.gui.dialog import connections_editor
from randovania.gui.lib import signal_handling

if TYPE_CHECKING:
    import pytestqt.qtbot  # type: ignore[import-untyped]

    from randovania.game_description.game_description import GameDescription


def test_build_no_changes(skip_qtbot: pytestqt.qtbot.QtBot, echoes_game_description: GameDescription) -> None:
    gd = echoes_game_description
    parent = QtWidgets.QWidget()
    skip_qtbot.addWidget(parent)

    # Setup
    def mk_req(name: str):
        return ResourceRequirement.with_data(gd.resource_database, ResourceType.ITEM, name, 1, False)

    requirement = RequirementOr(
        [
            RequirementAnd(
                [
                    mk_req("Dark"),
                    mk_req("Light"),
                ]
            ),
            mk_req("Power"),
            RequirementTemplate("Shoot Dark Beam"),
            NodeRequirement(
                NodeIdentifier.create(
                    "Great Temple",
                    "Transport A Access",
                    "Pickup (Missile)",
                )
            ),
        ]
    )

    # Run
    editor = connections_editor.ConnectionsEditor(parent, gd.resource_database, gd.region_list, requirement)
    result = editor.final_requirement

    # Assert
    assert result == requirement


@pytest.mark.parametrize("resource_type", [ResourceRequirement, RequirementOr, NodeRequirement, RequirementTemplate])
def test_build_change_root(
    skip_qtbot: pytestqt.qtbot.QtBot, echoes_game_description: GameDescription, resource_type: type[Requirement]
) -> None:
    gd = echoes_game_description
    parent = QtWidgets.QWidget()
    skip_qtbot.addWidget(parent)

    expected: Requirement | None

    if resource_type == ResourceRequirement:
        expected = ResourceRequirement.simple(gd.resource_database.item[0])

    elif resource_type == RequirementOr:
        expected = None

    elif resource_type == NodeRequirement:
        expected = NodeRequirement(
            next(
                node for node in echoes_game_description.region_list.iterate_nodes() if isinstance(node, ResourceNode)
            ).identifier
        )

    elif resource_type == RequirementTemplate:
        expected = RequirementTemplate(next(iter(gd.resource_database.requirement_template.keys())))

    else:
        raise NotImplementedError

    # Run
    editor = connections_editor.ConnectionsEditor(parent, gd.resource_database, gd.region_list, Requirement.trivial())
    signal_handling.set_combo_with_value(editor._root_editor.requirement_type_combo, resource_type)
    editor._root_editor._on_change_requirement_type()  # signal not emitted programmatically

    # Assert
    assert editor.final_requirement == expected
