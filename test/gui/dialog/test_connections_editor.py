from randovania.game_description.requirements import RequirementOr, RequirementAnd, ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.gui.dialog import connections_editor


def test_build_no_changes(skip_qtbot, echoes_resource_database):
    # Setup
    def mk_req(name: str):
        return ResourceRequirement.with_data(echoes_resource_database, ResourceType.ITEM, name, 1, False)

    requirement = RequirementOr([
        RequirementAnd([
            mk_req("Dark"),
            mk_req("Light"),
        ]),
        mk_req("Power"),
    ])

    # Run
    editor = connections_editor.ConnectionsEditor(None, echoes_resource_database,
                                                  requirement)
    skip_qtbot.addWidget(editor)
    result = editor.final_requirement

    # Assert
    assert result == requirement
