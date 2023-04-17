from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from randovania.gui.widgets.game_connection_window import GameConnectionWindow


@pytest.fixture(name="window")
def _window(skip_qtbot):
    game_connection = MagicMock()

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

