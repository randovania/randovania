import io
import json
from pathlib import Path

import pytest
from PySide2.QtWidgets import QDialog
from mock import AsyncMock, patch, ANY

import randovania.game_description.pretty_print
from randovania.game_description import data_reader, pretty_print
from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.requirements import Requirement
from randovania.gui.data_editor import DataEditorWindow


def test_apply_edit_connections_change(echoes_game_data,
                                       skip_qtbot,
                                       ):
    # Setup
    window = DataEditorWindow(echoes_game_data, None, False, True)
    skip_qtbot.addWidget(window)
    game = window.game_description

    landing_site = game.world_list.area_by_area_location(AreaLocation(1006255871, 1655756413))
    source = landing_site.node_with_name("Save Station")
    target = landing_site.node_with_name("Door to Service Access")

    # Run
    window.world_selector_box.setCurrentIndex(window.world_selector_box.findText("Temple Grounds (Sky Temple Grounds)"))
    window.area_selector_box.setCurrentIndex(window.area_selector_box.findText(landing_site.name))
    window._apply_edit_connections(source, target, Requirement.trivial())

    # Assert
    assert landing_site.connections[source][target] == Requirement.trivial()


def test_select_area_by_name(echoes_game_data,
                             skip_qtbot,
                             ):
    # Setup
    window = DataEditorWindow(echoes_game_data, None, False, True)
    skip_qtbot.addWidget(window)

    # Run
    window.focus_on_world("Torvus Bog")

    assert window.current_area.name != "Forgotten Bridge"
    window.focus_on_area("Forgotten Bridge")

    # Assert
    assert window.current_area.name == "Forgotten Bridge"


@pytest.mark.asyncio
@pytest.mark.parametrize("accept", [False, True])
@patch("randovania.gui.data_editor.ConnectionsEditor")
@patch("randovania.gui.data_editor.DataEditorWindow._apply_edit_connections", autospec=True)
async def test_open_edit_connection(mock_apply_edit_connections,
                                    mock_connections_editor,
                                    accept: bool,
                                    echoes_game_data,
                                    skip_qtbot,
                                    mocker,
                                    ):
    # Setup
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    window = DataEditorWindow(echoes_game_data, None, False, True)
    skip_qtbot.addWidget(window)

    editor = mock_connections_editor.return_value
    execute_dialog.return_value = QDialog.Accepted if accept else QDialog.Rejected

    # Run
    await window._open_edit_connection()

    # Assert
    mock_connections_editor.assert_called_once_with(window, window.resource_database, ANY)
    if accept:
        mock_apply_edit_connections.assert_called_once_with(window,
                                                            window.current_node,
                                                            window.current_connection_node,
                                                            editor.final_requirement)
    else:
        mock_apply_edit_connections.assert_not_called()


def test_create_node_and_save(tmp_path,
                              echoes_game_data,
                              skip_qtbot):
    # Setup
    tmp_path.joinpath("test-game", "game").mkdir(parents=True)
    tmp_path.joinpath("human-readable").mkdir()

    db_path = Path(tmp_path.joinpath("test-game", "game"))

    window = DataEditorWindow(echoes_game_data, db_path, True, True)
    skip_qtbot.addWidget(window)

    # Run
    window._do_create_node("Some Node")
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
