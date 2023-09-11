from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from PySide6 import QtWidgets

from randovania.game_connection.builder.connector_builder import ConnectorBuilder
from randovania.game_connection.builder.debug_connector_builder import DebugConnectorBuilder
from randovania.game_connection.builder.dolphin_connector_builder import DolphinConnectorBuilder
from randovania.game_connection.builder.dread_connector_builder import DreadConnectorBuilder
from randovania.game_connection.builder.nintendont_connector_builder import NintendontConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.games.game import RandovaniaGame
from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.widgets.game_connection_window import GameConnectionWindow
from randovania.interface_common.players_configuration import INVALID_UUID
from randovania.network_common import error

if TYPE_CHECKING:
    import pytest_mock
    from pytest_mock import MockerFixture

    from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog


@pytest.fixture()
def window(skip_qtbot, mocker):
    game_connection = MagicMock()
    game_connection.connection_builders = []
    window_manager = MagicMock(spec=WindowManager)
    network_client = MagicMock(spec=QtNetworkClient)

    result = GameConnectionWindow(window_manager, network_client, MagicMock(), game_connection)
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
async def test_add_connector_builder_dread(window: GameConnectionWindow, abort, mocker: pytest_mock.MockerFixture):
    # Setup
    window.game_connection.add_connection_builder = MagicMock()
    mocker.patch(
        "randovania.games.dread.gui.dialog.dread_connector_prompt_dialog.DreadConnectorPromptDialog.prompt",
        new_callable=AsyncMock,
        return_value=None if abort else "my_ip",
    )

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
def test_setup_builder_ui_all_builders(skip_qtbot, system, mocker: MockerFixture, is_dev_version, is_frozen):
    # Setup
    mocker.patch("platform.system", return_value=system)

    game_connection = MagicMock()
    game_connection.connection_builders = [
        DolphinConnectorBuilder(),
        NintendontConnectorBuilder("the_ip"),
        DebugConnectorBuilder(RandovaniaGame.BLANK.value),
    ]
    window_manager = MagicMock(spec=WindowManager)
    network_client = MagicMock(spec=QtNetworkClient)
    window = GameConnectionWindow(window_manager, network_client, MagicMock(), game_connection)
    skip_qtbot.addWidget(window)

    # Run
    window.setup_builder_ui()

    # Assert
    has_debug = ConnectorBuilderChoice.DEBUG.is_usable()
    if system == "Darwin":
        print(list(window.ui_for_builder.keys()))
        assert len(window.ui_for_builder) == 1 + has_debug
    else:
        assert not window._builder_actions[ConnectorBuilderChoice.DOLPHIN].isEnabled()
        assert len(window.ui_for_builder) == 2 + has_debug

    ui = window.ui_for_builder[game_connection.connection_builders[1]]
    if is_frozen:
        assert ui.important_message_menu is None
        assert ui.send_arbitrary_message_action is None
    else:
        assert ui.important_message_menu is not None
        assert ui.important_message_menu.isEnabled()
        assert ui.send_arbitrary_message_action is not None
        assert ui.send_arbitrary_message_action.isEnabled()


def test_update_builder_ui(skip_qtbot, mocker: MockerFixture):
    game_connection = MagicMock()
    game_connection.get_connector_for_builder.return_value = None

    game_connection.connection_builders = [
        builder_a := MagicMock(spec=ConnectorBuilder),
        builder_b := MagicMock(spec=ConnectorBuilder),
        builder_c := MagicMock(spec=ConnectorBuilder),
    ]
    builder_a.pretty_text = "ConnectorBuilder A"
    builder_a.get_status_message.return_value = None
    builder_b.pretty_text = "ConnectorBuilder B"
    builder_b.get_status_message.return_value = "Connecting!"
    builder_c.pretty_text = "ConnectorBuilder C"
    builder_c.get_status_message.return_value = None

    connector_a = MagicMock()
    connector_a.description.return_value = "Game A"
    connector_a.layout_uuid = INVALID_UUID
    connector_b = MagicMock()
    connector_b.description.return_value = "Game B"
    connector_c = MagicMock()
    connector_c.description.return_value = "Game C"

    window_manager = MagicMock(spec=WindowManager)
    network_client = MagicMock(spec=QtNetworkClient)

    # Run
    window = GameConnectionWindow(window_manager, network_client, MagicMock(), game_connection)
    assert window.ui_for_builder[builder_a].description.text() == "ConnectorBuilder A"
    assert window.ui_for_builder[builder_b].description.text() == "ConnectorBuilder B"
    assert window.ui_for_builder[builder_a].status.text() == "Not Connected."
    assert window.ui_for_builder[builder_b].status.text() == "Not Connected. Connecting!"

    game_connection.get_connector_for_builder = MagicMock(
        side_effect=lambda builder: {
            builder_a: connector_a,
            builder_b: connector_b,
            builder_c: connector_c,
        }[builder]
    )

    data_b = MagicMock()
    data_b.collected_locations = [10]
    data_b.uploaded_locations = [10]
    data_b.server_data = None
    data_c = MagicMock()
    data_c.collected_locations = [1, 5]
    data_c.uploaded_locations = [5]
    data_c.server_data.world_name = "TheWorld"
    data_c.server_data.session_name = "TheSession"

    window_manager.multiworld_client.database.get_data_for = MagicMock(
        side_effect=lambda uid: {
            connector_b.layout_uuid: data_b,
            connector_c.layout_uuid: data_c,
        }[uid]
    )
    window_manager.multiworld_client.get_world_sync_error = MagicMock(
        side_effect=lambda uid: (
            {
                connector_c.layout_uuid: error.ServerError(),
            }
        ).get(uid)
    )

    window.update_builder_ui()

    # Assert
    assert window.ui_for_builder[builder_a].status.text() == "Connected to Game A.\n\nSolo game."
    assert window.ui_for_builder[builder_b].status.text() == (
        "Connected to Game B.\n\n"
        "Unknown Multiworld game. 1 collected locations, with 0 pending delivery to other players."
    )
    assert window.ui_for_builder[builder_c].status.text() == (
        "Connected to Game C.\n\n"
        "World 'TheWorld' for session 'TheSession'. 2 collected locations, "
        "with 1 pending delivery to other players.\n\n"
        "**\\*\\*Received Internal Server Error on last delivery.\\*\\***"
    )
    assert not window.ui_for_builder[builder_a].open_session_action.isEnabled()
    assert not window.ui_for_builder[builder_b].open_session_action.isEnabled()
    assert window.ui_for_builder[builder_c].open_session_action.isEnabled()


@pytest.mark.parametrize(
    "result",
    [
        QtWidgets.QDialog.DialogCode.Accepted,
        QtWidgets.QDialog.DialogCode.Rejected,
    ],
)
async def test_prompt_for_text(window: GameConnectionWindow, mocker, result):
    def side_effect(dialog: TextPromptDialog):
        dialog.prompt_edit.setText("UserInput")
        assert dialog.windowTitle() == "Title"
        return result

    mock_execute_dialog = mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock, side_effect=side_effect
    )
    response = await window._prompt_for_text("Title", "Label")

    if result == QtWidgets.QDialog.DialogCode.Accepted:
        assert response == "UserInput"
    else:
        assert response is None
    mock_execute_dialog.assert_awaited_once()


@pytest.mark.parametrize(
    "result",
    [
        QtWidgets.QDialog.DialogCode.Accepted,
        QtWidgets.QDialog.DialogCode.Rejected,
    ],
)
async def test_prompt_for_game(window: GameConnectionWindow, mocker, result):
    def side_effect(dialog: QtWidgets.QInputDialog):
        dialog.setTextValue(RandovaniaGame.BLANK.long_name)
        return result

    mock_execute_dialog = mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock, side_effect=side_effect
    )
    response = await window._prompt_for_game("Title", "Label")

    if result == QtWidgets.QDialog.DialogCode.Accepted:
        assert response == RandovaniaGame.BLANK
    else:
        assert response is None
    mock_execute_dialog.assert_awaited_once()


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
    assert result == "Foo"


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
    builder = MagicMock(spec=ConnectorBuilder)
    window.window_manager.ensure_multiplayer_session_window = AsyncMock()
    layout_uuid = window.game_connection.get_connector_for_builder.return_value.layout_uuid

    # run
    await window._attempt_join(builder)

    # assert
    window.game_connection.get_connector_for_builder.assert_called_once_with(builder)
    window._check_session_data.assert_called_once_with(layout_uuid)
    window.window_manager.ensure_multiplayer_session_window.assert_called_once_with(
        window.network_client, window._check_session_data.return_value, window.options
    )


async def test_attempt_join_not_authorized(window: GameConnectionWindow, mocker):
    # setup
    builder = MagicMock(spec=ConnectorBuilder)
    window.network_client.ensure_logged_in = AsyncMock(return_value=True)
    window._check_session_data = MagicMock()
    layout_uuid = window.game_connection.get_connector_for_builder.return_value.layout_uuid
    window.window_manager.ensure_multiplayer_session_window = AsyncMock()
    window.network_client.listen_to_session = AsyncMock(side_effect=error.NotAuthorizedForActionError())
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    # run
    await window._attempt_join(builder)

    # assert
    window._check_session_data.assert_called_once_with(layout_uuid)
    window.window_manager.ensure_multiplayer_session_window.assert_not_called()
    mock_warning.assert_awaited_once()
