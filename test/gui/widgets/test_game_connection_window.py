from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, ANY, patch

import pytest
from PySide6 import QtWidgets
from pytest_mock import MockerFixture

from randovania.game_connection.builder.debug_connector_builder import DebugConnectorBuilder
from randovania.game_connection.builder.dolphin_connector_builder import DolphinConnectorBuilder
from randovania.game_connection.builder.dread_connector_builder import DreadConnectorBuilder
from randovania.game_connection.builder.nintendont_connector_builder import NintendontConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.games.game import RandovaniaGame
from randovania.gui.widgets.game_connection_window import GameConnectionWindow


@pytest.fixture(name="window")
def _window(skip_qtbot):
    game_connection = MagicMock()
    game_connection.connection_builders = []

    result = GameConnectionWindow(game_connection)
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

    window = GameConnectionWindow(game_connection)
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
    def side_effect(dialog: QtWidgets.QInputDialog):
        dialog.setTextValue("UserInput")
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
