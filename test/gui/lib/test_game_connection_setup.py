from pathlib import Path

import pytest
from PySide2 import QtWidgets
from mock import MagicMock, AsyncMock

from randovania.game_connection.executor.dolphin_executor import DolphinExecutor
from randovania.game_connection.game_connection import GameConnection
from randovania.gui.lib.game_connection_setup import GameConnectionSetup


@pytest.fixture(name="setup")
def _setup(skip_qtbot):
    parent = QtWidgets.QWidget()
    skip_qtbot.addWidget(parent)
    tool = QtWidgets.QToolButton(parent)
    label = QtWidgets.QLabel(parent)

    result = GameConnectionSetup(parent, label, GameConnection(DolphinExecutor()), MagicMock())
    result.setup_tool_button_menu(tool)

    return result


@pytest.mark.parametrize("nintendont_ip", [None, "localhost", "192.168.0.1"])
@pytest.mark.asyncio
async def test_on_use_nintendont_backend_accept(setup, mocker, nintendont_ip):
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                       return_value=QtWidgets.QDialog.Accepted)
    setup.options.nintendont_ip = nintendont_ip
    old_executor = setup.game_connection.executor

    # Run
    await setup.on_use_nintendont_backend()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    dialog: QtWidgets.QInputDialog = mock_execute_dialog.mock_calls[0].args[0]
    if nintendont_ip is not None:
        assert dialog.textValue() == nintendont_ip
        assert setup.game_connection.executor is not old_executor
        assert setup.use_nintendont_backend.isChecked()
        assert setup.use_nintendont_backend.text() == f"Nintendont: {nintendont_ip}"

    else:
        assert dialog.textValue() == ""
        assert setup.game_connection.executor is old_executor


@pytest.mark.asyncio
async def test_on_upload_nintendont_action_no_dol(setup, mocker, tmpdir):
    mocker.patch("randovania.gui.lib.game_connection_setup.get_data_path", return_value=Path(tmpdir))
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    # Run
    await setup.on_upload_nintendont_action()

    # Assert
    execute_dialog.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_upload_nintendont_action_with_dol(setup, mocker, tmpdir):
    mock_message_box = mocker.patch("PySide2.QtWidgets.QMessageBox")
    mocker.patch("randovania.gui.lib.game_connection_setup.get_data_path", return_value=Path(tmpdir))
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_upload = mocker.patch("wiiload.upload_file", new_callable=AsyncMock)

    nintendont_path = Path(tmpdir).joinpath("nintendont", "boot.dol")
    nintendont_path.parent.mkdir()
    nintendont_path.write_bytes(b"FOO")

    # Run
    await setup.on_upload_nintendont_action()

    # Assert
    execute_dialog.assert_not_awaited()
    mock_upload.assert_awaited_once_with(nintendont_path, [], setup.options.nintendont_ip)
    mock_message_box.assert_called_once()
    mock_message_box.return_value.show.assert_called_once_with()
