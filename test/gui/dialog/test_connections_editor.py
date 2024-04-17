from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.gui.dialog import connections_editor

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
        ]
    )

    # Run
    editor = connections_editor.ConnectionsEditor(parent, gd.resource_database, gd.region_list, requirement)
    result = editor.final_requirement

    # Assert
    assert result == requirement
