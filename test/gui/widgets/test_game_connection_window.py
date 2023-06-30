from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, ANY

import pytest
from PySide6 import QtWidgets
from pytest_mock import MockerFixture
from PySide6 import QtWidgets, QtGui

from randovania.game_connection.builder.debug_connector_builder import DebugConnectorBuilder
from randovania.game_connection.builder.dolphin_connector_builder import DolphinConnectorBuilder
from randovania.game_connection.builder.dread_connector_builder import DreadConnectorBuilder
from randovania.game_connection.builder.nintendont_connector_builder import NintendontConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog
from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.gui.widgets.game_connection_window import BuilderUi, GameConnectionWindow
from randovania.interface_common.players_configuration import INVALID_UUID
from randovania.network_common import error


@pytest.fixture(name="window")
def _window(skip_qtbot, mocker):
    game_connection = MagicMock()
    game_connection.connection_builders = []
    parent = QtWidgets.QWidget()
    network_client = MagicMock(QtNetworkClient)

    result = GameConnectionWindow(parent, network_client, MagicMock(), game_connection)
    skip_qtbot.addWidget(result)

    return result


async def test_on_upload_nintendont_action_no_dol(window: GameConnectionWindow, mocker, tmpdir):
    mocker.patch("randovania.get_data_path", return_value=Path(tmpdir))
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    builder = MagicMock()

    # Run
    await window.on_upload_nintendont_action(builder)

    # Assert
    execute_dialog.assert_awaited_once()


async def test_on_upload_nintendont_action_with_dol(window: GameConnectionWindow, mocker, tmpdir):
    mock_message_box = mocker.patch("PySide6.QtWidgets.QMessageBox")
    mocker.patch("randovania.get_data_path", return_value=Path(tmpdir))
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_upload = mocker.patch("wiiload.upload_file", new_callable=AsyncMock)
    builder = MagicMock()

    nintendont_path = Path(tmpdir).joinpath("nintendont", "boot.dol")
    nintendont_path.parent.mkdir()
    nintendont_path.write_bytes(b"FOO")

    # Run
    await window.on_upload_nintendont_action(builder)

    # Assert
    execute_dialog.assert_not_awaited()
    mock_upload.assert_awaited_once_with(nintendont_path, [], builder.ip)
    mock_message_box.assert_called_once()
    mock_message_box.return_value.show.assert_called_once_with()


async def test_add_connector_builder_dolphin(window: GameConnectionWindow):
    window.game_connection.add_connection_builder = MagicMock()

    # Run
    await window._add_connector_builder(ConnectorBuilderChoice.DOLPHIN)

    # Assert
    window.game_connection.add_connection_builder.assert_called_once_with(ANY)
    assert isinstance(window.game_connection.add_connection_builder.call_args[0][0], DolphinConnectorBuilder)


@pytest.mark.parametrize("abort", [False, True])
async def test_add_connector_builder_nintendont(window: GameConnectionWindow, abort):
    # Setup
    window.game_connection.add_connection_builder = MagicMock()
    window._prompt_for_text = AsyncMock(return_value=None if abort else "my_ip")

    # Run
    await window._add_connector_builder(ConnectorBuilderChoice.NINTENDONT)

    # Assert
    if abort:
        window.game_connection.add_connection_builder.assert_not_called()
    else:
        window.game_connection.add_connection_builder.assert_called_once_with(ANY)
        assert isinstance(window.game_connection.add_connection_builder.call_args[0][0], NintendontConnectorBuilder)
        assert window.game_connection.add_connection_builder.call_args[0][0].ip == "my_ip"


@pytest.mark.parametrize("abort", [False, True])
async def test_add_connector_builder_debug(window: GameConnectionWindow, abort):
    # Setup
    window.game_connection.add_connection_builder = MagicMock()
    window._prompt_for_game = AsyncMock(return_value=None if abort else RandovaniaGame.BLANK)

    # Run
    await window._add_connector_builder(ConnectorBuilderChoice.DEBUG)

    # Assert
    if abort:
        window.game_connection.add_connection_builder.assert_not_called()
    else:
        window.game_connection.add_connection_builder.assert_called_once_with(ANY)
        assert isinstance(window.game_connection.add_connection_builder.call_args[0][0], DebugConnectorBuilder)
        assert window.game_connection.add_connection_builder.call_args[0][0].target_game == RandovaniaGame.BLANK


@pytest.mark.parametrize("abort", [False, True])
async def test_add_connector_builder_dread(window: GameConnectionWindow, abort):
    # Setup
    window.game_connection.add_connection_builder = MagicMock()
    window._prompt_for_text = AsyncMock(return_value=None if abort else "my_ip")

    # Run
    await window._add_connector_builder(ConnectorBuilderChoice.DREAD)

    # Assert
    if abort:
        window.game_connection.add_connection_builder.assert_not_called()
    else:
        window.game_connection.add_connection_builder.assert_called_once_with(ANY)
        assert isinstance(window.game_connection.add_connection_builder.call_args[0][0], DreadConnectorBuilder)
        assert window.game_connection.add_connection_builder.call_args[0][0].ip == "my_ip"


@pytest.mark.parametrize("system", ["Darwin", "Windows"])
def test_setup_builder_ui_all_builders(skip_qtbot, system, mocker: MockerFixture, is_dev_version):
    # Setup
    mocker.patch("randovania.is_frozen", return_value=False)
    mocker.patch("platform.system", return_value=system)

    game_connection = MagicMock()
    game_connection.connection_builders = [
        DolphinConnectorBuilder(),
        NintendontConnectorBuilder("the_ip"),
        DebugConnectorBuilder(RandovaniaGame.BLANK.value),
    ]
    parent = QtWidgets.QWidget()
    network_client = MagicMock(QtNetworkClient)
    window = GameConnectionWindow(parent, network_client, MagicMock(), game_connection)
    skip_qtbot.addWidget(window)

    # Run
    window.setup_builder_ui()

    # Assert
    if system == "Darwin":
        assert len(window.ui_for_builder) == 1 + is_dev_version
    else:
        assert not window._builder_actions[ConnectorBuilderChoice.DOLPHIN].isEnabled()
        assert len(window.ui_for_builder) == 2 + is_dev_version


@pytest.mark.parametrize("result", [
    QtWidgets.QDialog.DialogCode.Accepted,
    QtWidgets.QDialog.DialogCode.Rejected,
])
async def test_prompt_for_text(window: GameConnectionWindow, mocker, result):
    def side_effect(dialog: TextPromptDialog):
        dialog.prompt_edit.setText("UserInput")
        assert dialog.windowTitle() == "Title"
        return result

    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                       side_effect=side_effect)
    response = await window._prompt_for_text("Title", "Label")

    if result == QtWidgets.QDialog.DialogCode.Accepted:
        assert response == "UserInput"
    else:
        assert response is None
    mock_execute_dialog.assert_awaited_once()


@pytest.mark.parametrize("result", [
    QtWidgets.QDialog.DialogCode.Accepted,
    QtWidgets.QDialog.DialogCode.Rejected,
])
async def test_prompt_for_game(window: GameConnectionWindow, mocker, result):
    def side_effect(dialog: QtWidgets.QInputDialog):
        dialog.setTextValue(RandovaniaGame.BLANK.long_name)
        return result

    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                       side_effect=side_effect)
    response = await window._prompt_for_game("Title", "Label")

    if result == QtWidgets.QDialog.DialogCode.Accepted:
        assert response == RandovaniaGame.BLANK
    else:
        assert response is None
    mock_execute_dialog.assert_awaited_once()


def test_add_session_action_no_layout_uuid(window: GameConnectionWindow):
    # setup
    window._get_valid_uuid = MagicMock()
    window._get_valid_uuid.return_value = None
    builder = MagicMock()
    ui = MagicMock(BuilderUi)
    # run
    window._add_session_action(builder, ui)
    # assert
    ui.remove_session_button.assert_not_called()
    ui.add_session_button.assert_not_called()


def test_add_session_action_new_layout_uuid(window: GameConnectionWindow):
    # setup
    window._get_valid_uuid = MagicMock()
    window._get_valid_uuid.return_value = MagicMock()
    builder = MagicMock()
    ui = MagicMock(BuilderUi)
    window.ui_for_builder = {builder: ui}
    # run
    window._add_session_action(builder, ui)
    # assert
    ui.remove_session_button.assert_not_called()
    ui.add_session_button.assert_called_once()


def test_add_session_action_fast_new_layout_uuid(window: GameConnectionWindow):
    # setup
    window._get_valid_uuid = MagicMock()
    window._get_valid_uuid.return_value = MagicMock()
    builder = MagicMock()
    ui = MagicMock(BuilderUi)
    layout_uuid = MagicMock()
    window.ui_for_builder = {builder: ui}
    window.layout_uuid_for_builder = {builder: layout_uuid}

    # run
    window._add_session_action(builder, ui)

    # assert
    ui.remove_session_button.assert_called_once()
    ui.add_session_button.assert_called_once()


def test_add_session_action_removed_layout_uuid(window: GameConnectionWindow):
    # setup
    window._get_valid_uuid = MagicMock()
    window._get_valid_uuid.return_value = None
    builder = MagicMock()
    ui = MagicMock(BuilderUi)
    layout_uuid = MagicMock()
    window.ui_for_builder = {builder: ui}
    window.layout_uuid_for_builder = {builder: layout_uuid}

    # run
    window._add_session_action(builder, ui)

    # assert
    ui.remove_session_button.assert_called_once()
    ui.add_session_button.assert_not_called()


def test_get_valid_uuid_no_remote_connector(window: GameConnectionWindow):
    # setup
    builder = MagicMock()
    window.game_connection.remote_connectors = {}

    # run
    result = window._get_valid_uuid(builder)

    # assert
    assert result is None


def test_get_valid_uuid_invalid_uuid(window: GameConnectionWindow):
    # setup
    builder = MagicMock()
    remote_connector = MagicMock()
    remote_connector.layout_uuid = INVALID_UUID
    window.game_connection.remote_connectors = {builder: remote_connector}

    # run
    result = window._get_valid_uuid(builder)

    # assert
    assert result is None


def test_get_valid_uuid_valid_uuid(window: GameConnectionWindow):
    # setup
    builder = MagicMock()
    layout_uuid = MagicMock()
    remote_connector = MagicMock()
    remote_connector.layout_uuid = layout_uuid
    window.game_connection.remote_connectors = {builder: remote_connector}

    # run
    result = window._get_valid_uuid(builder)

    # assert
    assert result is layout_uuid


def test_check_session_data_no_data(window: GameConnectionWindow):
    # setup
    world_database = MagicMock()
    world_data = MagicMock()
    world_data.server_data = None
    world_database.get_data_for = MagicMock(return_value=world_data)
    window.world_database = world_database
    
    # run
    result = window._check_session_data(MagicMock())

    # assert
    assert result is None


def test_check_session_data_with_data(window: GameConnectionWindow):
    # setup
    world_database = MagicMock()
    world_data = MagicMock()
    server_data = MagicMock()
    server_data.session_id = "Foo"
    world_data.server_data = server_data
    world_database.get_data_for = MagicMock(return_value=world_data)
    window.world_database = world_database
    
    # run
    result = window._check_session_data(MagicMock())

    # assert
    assert result is "Foo"


async def test_attempt_join_no_login(window: GameConnectionWindow):
    # setup
    window.network_client.ensure_logged_in = AsyncMock(return_value=False)
    window._check_session_data = MagicMock()

    # run
    await window._attempt_join(MagicMock())

    # assert
    window._check_session_data.assert_not_called()


async def test_attempt_join_success(window: GameConnectionWindow):
    # setup
    window.network_client.ensure_logged_in = AsyncMock(return_value=True)
    window._check_session_data = MagicMock()
    layout_uuid = MagicMock()
    window.window_manager.ensure_multiplayer_session_window = AsyncMock()
    # run
    await window._attempt_join(layout_uuid)

    # assert
    window._check_session_data.assert_called_once_with(layout_uuid)
    window.window_manager.ensure_multiplayer_session_window.assert_called_once()

async def test_attempt_join_not_authorized(window: GameConnectionWindow, mocker):
    # setup
    window.network_client.ensure_logged_in = AsyncMock(return_value=True)
    window._check_session_data = MagicMock()
    layout_uuid = MagicMock()
    window.window_manager.ensure_multiplayer_session_window = AsyncMock()
    window.network_client.listen_to_session = AsyncMock(side_effect=error.NotAuthorizedForAction())
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    # run
    await window._attempt_join(layout_uuid)

    # assert
    window._check_session_data.assert_called_once_with(layout_uuid)
    window.window_manager.ensure_multiplayer_session_window.assert_not_called()
    mock_warning.assert_awaited_once()

@pytest.mark.parametrize("case", [i for i in range(2)])
def test_builder_ui_add_session_button(window: GameConnectionWindow, case: int):
    ui = BuilderUi(window.builders_group)

    if case == 0:
        result = ui.add_session_button()
        assert isinstance(result, QtGui.QAction)
    elif case == 1:
        ui.join_session = (MagicMock(), MagicMock())
        result = ui.add_session_button()
        assert ui.join_session[1] == result


def test_builder_ui_remove_session_button(window: GameConnectionWindow):
    ui = BuilderUi(window.builders_group)
    ui.add_session_button()
    ui.remove_session_button()
    assert ui.join_session is None
