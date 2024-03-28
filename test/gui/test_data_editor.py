from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from PySide6 import QtWidgets

from randovania.game_description import data_reader, pretty_print
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.node import NodeContext, NodeLocation
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.games import default_data
from randovania.games.game import RandovaniaGame
from randovania.gui.data_editor import DataEditorWindow, _ui_patch_and_simplify

if TYPE_CHECKING:
    import pytest_mock


def test_select_area_by_name(
    echoes_game_data,
    skip_qtbot,
):
    # Setup
    window = DataEditorWindow(echoes_game_data, None, False, True)
    skip_qtbot.addWidget(window)

    # Run
    window.focus_on_region_by_name("Torvus Bog")

    assert window.current_area.name != "Forgotten Bridge"
    window.focus_on_area_by_name("Forgotten Bridge")

    # Assert
    assert window.current_area.name == "Forgotten Bridge"


@pytest.mark.parametrize("accept", [False, True])
async def test_open_edit_connection(
    accept: bool,
    echoes_game_data,
    skip_qtbot,
    mocker: pytest_mock.MockerFixture,
):
    # Setup
    mock_connections_editor = mocker.patch("randovania.gui.data_editor.ConnectionsEditor")
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    window = DataEditorWindow(echoes_game_data, None, False, True)
    window.editor = MagicMock()
    skip_qtbot.addWidget(window)

    editor = mock_connections_editor.return_value
    execute_dialog.return_value = (
        QtWidgets.QDialog.DialogCode.Accepted if accept else QtWidgets.QDialog.DialogCode.Rejected
    )

    # Run
    await window._open_edit_connection()

    # Assert
    mock_connections_editor.assert_called_once_with(window, window.resource_database, window.region_list, ANY)
    if accept:
        window.editor.edit_connections.assert_called_once_with(
            window.current_area, window.current_node, window.current_connection_node, editor.final_requirement
        )
    else:
        window.editor.edit_connections.assert_not_called()


def test_create_node_and_save(tmp_path, echoes_game_data, skip_qtbot):
    # Setup
    tmp_path.joinpath("test-game", "game").mkdir(parents=True)
    tmp_path.joinpath("human-readable").mkdir()

    db_path = Path(tmp_path.joinpath("test-game", "game"))

    window = DataEditorWindow(echoes_game_data, db_path, True, True)
    window.set_warning_dialogs_disabled(True)
    skip_qtbot.addWidget(window)

    # Run
    window._do_create_node("Some Node", None)
    window._save_as_internal_database()

    # Assert
    exported_data = data_reader.read_split_file(db_path)
    exported_game = data_reader.decode_data(exported_data)

    pretty_print.write_human_readable_game(exported_game, tmp_path.joinpath("human-readable"))
    new_files = {f.name: f.read_text("utf-8") for f in tmp_path.joinpath("human-readable").glob("*.txt")}

    existing_files = {f.name: f.read_text("utf-8") for f in tmp_path.joinpath("test-game", "game").glob("*.txt")}

    assert list(new_files.keys()) == list(existing_files.keys())
    assert new_files == existing_files


def test_save_database_integrity_failure(tmp_path, echoes_game_data, skip_qtbot, mocker):
    # Setup
    mock_find_database_errors = mocker.patch(
        "randovania.game_description.integrity_check.find_database_errors", return_value=["DB Errors", "Unknown"]
    )
    mock_write_human_readable_game = mocker.patch("randovania.game_description.pretty_print.write_human_readable_game")
    mock_create_new = mocker.patch("randovania.gui.lib.scroll_message_box.ScrollMessageBox.create_new")
    mock_create_new.return_value.exec_.return_value = QtWidgets.QMessageBox.No

    tmp_path.joinpath("test-game", "game").mkdir(parents=True)
    tmp_path.joinpath("human-readable").mkdir()

    db_path = Path(tmp_path.joinpath("test-game", "game"))

    window = DataEditorWindow(echoes_game_data, db_path, True, True)
    skip_qtbot.addWidget(window)

    # Run
    window._save_as_internal_database()

    # Assert
    mock_find_database_errors.assert_called_once_with(window.game_description)
    mock_write_human_readable_game.assert_not_called()
    mock_create_new.assert_called_once_with(
        window,
        QtWidgets.QMessageBox.Icon.Critical,
        "Integrity Check",
        "Database has the following errors:\n\nDB Errors\n\nUnknown\n\nIgnore?",
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        QtWidgets.QMessageBox.No,
    )


def test_on_filters_changed_view_mode(tmp_path, mocker, skip_qtbot):
    db_path = Path(tmp_path.joinpath("test-game", "game"))
    game_data = default_data.read_json_then_binary(RandovaniaGame.BLANK)[1]

    window = DataEditorWindow(game_data, db_path, True, False)
    skip_qtbot.addWidget(window)

    # Disable the layer
    found = False
    for (trick, trick_check), trick_combo in window.connection_filters.tricks.items():
        if trick.long_name == "Combat":
            trick_check.setChecked(True)
            trick_combo.setCurrentIndex(1)
            found = True

    assert found
    window.connection_filters.layer_checks[1].setChecked(False)

    window.focus_on_region_by_name("Intro")
    window.focus_on_area_by_name("Boss Arena")

    assert window.current_area.node_with_name("Pickup (Free Loot)") is None


def test_create_new_dock(skip_qtbot, tmp_path, blank_game_data):
    db_path = Path(tmp_path.joinpath("test-game", "game"))
    game_data = default_data.read_json_then_binary(RandovaniaGame.BLANK)[1]

    window = DataEditorWindow(game_data, db_path, True, True)
    window.set_warning_dialogs_disabled(True)
    skip_qtbot.addWidget(window)

    window.focus_on_area_by_name("Back-Only Lock Room")
    current_area = window.current_area
    target_area = window.game_description.region_list.area_by_area_location(AreaIdentifier("Intro", "Explosive Depot"))

    assert current_area.node_with_name("Dock to Explosive Depot") is None
    assert target_area.node_with_name("Dock to Back-Only Lock Room") is None

    # Run
    window._create_new_dock(NodeLocation(0.0, 0.0, 0.0), target_area)

    # Assert
    new_node = current_area.node_with_name("Dock to Explosive Depot")
    assert new_node is not None
    assert window.current_node is new_node

    assert target_area.node_with_name("Dock to Back-Only Lock Room") is not None


def test_ui_patch_and_simplify_trivial_in_or(echoes_resource_database):
    # Trivial in Or
    assert (
        _ui_patch_and_simplify(
            RequirementOr(
                [
                    Requirement.trivial(),
                    Requirement.impossible(),
                ],
                comment="COM",
            ),
            NodeContext(None, ResourceCollection(), echoes_resource_database, None),
        )
        == Requirement.trivial()
    )


def test_ui_patch_and_simplify_impossible_in_and(echoes_resource_database):
    # Impossible in And
    assert (
        _ui_patch_and_simplify(
            RequirementAnd(
                [
                    Requirement.trivial(),
                    Requirement.impossible(),
                ],
                comment="COM",
            ),
            NodeContext(None, ResourceCollection(), echoes_resource_database, None),
        )
        == Requirement.impossible()
    )


def test_ui_patch_and_simplify_remove_present_resources(echoes_resource_database):
    db = echoes_resource_database

    # Remove present resources, plus trivial in And
    col = ResourceCollection.with_database(db)
    col.set_resource(db.get_item("Seekers"), 1)
    assert _ui_patch_and_simplify(
        RequirementAnd(
            [
                ResourceRequirement.simple(db.get_item("Seekers")),
                ResourceRequirement.simple(db.get_item("ScrewAttack")),
                Requirement.trivial(),
            ],
            comment="COM",
        ),
        NodeContext(None, col, db, None),
    ) == RequirementAnd([ResourceRequirement.simple(db.get_item("ScrewAttack"))])


def test_ui_patch_and_simplify_template(echoes_resource_database):
    db = echoes_resource_database

    def context(collection):
        return NodeContext(None, collection, db, None)

    assert _ui_patch_and_simplify(
        RequirementTemplate("Use Screw Attack (No Space Jump)"), context(ResourceCollection())
    ) == RequirementTemplate("Use Screw Attack (No Space Jump)")

    col = ResourceCollection.with_database(db)
    col.set_resource(db.get_item("ScrewAttack"), 1)
    assert _ui_patch_and_simplify(
        RequirementTemplate("Use Screw Attack (No Space Jump)"), context(col)
    ) == RequirementAnd([ResourceRequirement.simple(db.get_item("MorphBall"))])
