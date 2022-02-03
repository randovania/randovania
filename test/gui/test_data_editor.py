from pathlib import Path

import pytest
from PySide2 import QtWidgets
from mock import AsyncMock, patch, ANY, MagicMock

from randovania.game_description import data_reader, pretty_print
from randovania.gui.data_editor import DataEditorWindow


def test_select_area_by_name(echoes_game_data,
                             skip_qtbot,
                             ):
    # Setup
    window = DataEditorWindow(echoes_game_data, None, False, True)
    skip_qtbot.addWidget(window)

    # Run
    window.focus_on_world_by_name("Torvus Bog")

    assert window.current_area.name != "Forgotten Bridge"
    window.focus_on_area_by_name("Forgotten Bridge")

    # Assert
    assert window.current_area.name == "Forgotten Bridge"


@pytest.mark.parametrize("accept", [False, True])
@patch("randovania.gui.data_editor.ConnectionsEditor")
async def test_open_edit_connection(mock_connections_editor: MagicMock,
                                    accept: bool,
                                    echoes_game_data,
                                    skip_qtbot,
                                    mocker,
                                    ):
    # Setup
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    window = DataEditorWindow(echoes_game_data, None, False, True)
    window.editor = MagicMock()
    skip_qtbot.addWidget(window)

    editor = mock_connections_editor.return_value
    execute_dialog.return_value = QtWidgets.QDialog.Accepted if accept else QtWidgets.QDialog.Rejected

    # Run
    await window._open_edit_connection()

    # Assert
    mock_connections_editor.assert_called_once_with(window, window.resource_database, ANY)
    if accept:
        window.editor.edit_connections.assert_called_once_with(
            window.current_area,
            window.current_node,
            window.current_connection_node,
            editor.final_requirement
        )
    else:
        window.editor.edit_connections.assert_not_called()


def test_create_node_and_save(tmp_path,
                              echoes_game_data,
                              skip_qtbot):
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
    new_files = {f.name: f.read_text("utf-8")
                 for f in tmp_path.joinpath("human-readable").glob("*.txt")}

    existing_files = {f.name: f.read_text("utf-8")
                      for f in tmp_path.joinpath("test-game", "game").glob("*.txt")}

    assert list(new_files.keys()) == list(existing_files.keys())
    assert new_files == existing_files


def test_save_database_integrity_failure(tmp_path, echoes_game_data, skip_qtbot, mocker):
    # Setup
    mock_find_database_errors = mocker.patch("randovania.game_description.integrity_check.find_database_errors",
                                             return_value=["DB Errors", "Unknown"])
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
        window, QtWidgets.QMessageBox.Icon.Critical, "Integrity Check",
        "Database has the following errors:\n\nDB Errors\n\nUnknown\n\nIgnore?",
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        QtWidgets.QMessageBox.No
    )
