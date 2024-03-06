from __future__ import annotations

from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.gui.dialog import connections_editor


def test_build_no_changes(skip_qtbot, echoes_game_description):
    gd = echoes_game_description

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
    editor = connections_editor.ConnectionsEditor(None, gd.resource_database, gd.region_list, requirement)
    skip_qtbot.addWidget(editor)
    result = editor.final_requirement

    # Assert
    assert result == requirement
