import io
import json
from pathlib import Path
from unittest.mock import patch, ANY

import pytest
from PySide2.QtWidgets import QDialog

from randovania.game_description import data_reader, data_writer
from randovania.game_description.requirements import Requirement
from randovania.gui.data_editor import DataEditorWindow


def test_apply_edit_connections_change(echoes_game_data,
                                       skip_qtbot,
                                       ):
    # Setup
    window = DataEditorWindow(echoes_game_data, True)
    skip_qtbot.addWidget(window)
    game = window.game_description

    landing_site = game.world_list.area_by_asset_id(1655756413)
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
    window = DataEditorWindow(echoes_game_data, True)
    skip_qtbot.addWidget(window)

    # Run
    window.focus_on_world("Torvus Bog")

    assert window.current_area.name != "Forgotten Bridge"
    window.focus_on_area("Forgotten Bridge")

    # Assert
    assert window.current_area.name == "Forgotten Bridge"


@pytest.mark.parametrize("accept", [False, True])
@patch("randovania.gui.data_editor.ConnectionsEditor")
@patch("randovania.gui.data_editor.DataEditorWindow._apply_edit_connections", autospec=True)
def test_open_edit_connection(mock_apply_edit_connections,
                              mock_connections_editor,
                              accept: bool,
                              echoes_game_data,
                              skip_qtbot,
                              ):
    # Setup
    window = DataEditorWindow(echoes_game_data, True)
    skip_qtbot.addWidget(window)

    editor = mock_connections_editor.return_value
    editor.exec_.return_value = QDialog.Accepted if accept else QDialog.Rejected

    # Run
    window._open_edit_connection()

    # Assert
    mock_connections_editor.assert_called_once_with(window, window.resource_database, ANY)
    if accept:
        mock_apply_edit_connections.assert_called_once_with(window,
                                                            window.current_node,
                                                            window.current_connection_node,
                                                            editor.final_requirement)
    else:
        mock_apply_edit_connections.assert_not_called()


@patch("randovania.gui.data_editor.default_data.prime2_json_path", autospec=True)
@patch("randovania.gui.data_editor.default_data.prime2_human_readable_path", autospec=True)
def test_create_node_and_save(mock_prime2_human_readable_path,
                              mock_prime2_json_path,
                              tmpdir,
                              echoes_game_data,
                              skip_qtbot):
    # Setup
    mock_prime2_human_readable_path.return_value = Path(tmpdir).joinpath("human")
    mock_prime2_json_path.return_value = Path(tmpdir).joinpath("database")

    window = DataEditorWindow(echoes_game_data, True)
    skip_qtbot.addWidget(window)

    # Run
    window._do_create_node("Some Node")
    window._save_as_internal_database()

    # Assert
    with mock_prime2_json_path.return_value.open() as data_file:
        exported_data = json.load(data_file)
    exported_game = data_reader.decode_data(exported_data)

    output = io.StringIO()
    data_writer.write_human_readable_world_list(exported_game, output)

    assert mock_prime2_human_readable_path.return_value.read_text("utf-8") == output.getvalue()
