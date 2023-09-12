from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PySide6 import QtWidgets
from PySide6.QtWidgets import QDialog

from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.gui.main_online_interaction import OnlineInteractions
from randovania.interface_common.options import Options


@pytest.fixture()
def default_online_interactions(skip_qtbot, preset_manager) -> OnlineInteractions:
    main_window = MagicMock()
    parent = QtWidgets.QWidget()
    network_client = MagicMock(QtNetworkClient, autospec=True)
    skip_qtbot.add_widget(parent)

    return OnlineInteractions(parent, preset_manager, network_client, main_window, Options(MagicMock()))


@pytest.mark.parametrize("refresh_success", [False, True])
async def test_browse_for_game_session(skip_qtbot, default_online_interactions, mocker, refresh_success):
    # Setup
    mock_game_session_browser: MagicMock = mocker.patch(
        "randovania.gui.main_online_interaction.MultiplayerSessionBrowserDialog", autospec=True
    )
    mock_ensure_session_window = AsyncMock(return_value=MagicMock())
    default_online_interactions.window_manager.ensure_multiplayer_session_window = mock_ensure_session_window

    default_online_interactions._ensure_logged_in = AsyncMock(return_value=True)
    message_box = mocker.patch("PySide6.QtWidgets.QMessageBox")

    mock_execute_dialog: AsyncMock = mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock
    )
    mock_execute_dialog.return_value = QtWidgets.QDialog.DialogCode.Accepted
    mock_game_session_browser.return_value.refresh = AsyncMock(return_value=refresh_success)

    # Run
    await default_online_interactions._browse_for_session()

    # Assert
    mock_game_session_browser.assert_called_once_with(default_online_interactions.network_client)
    mock_game_session_browser.return_value.refresh.assert_awaited_once_with()
    message_box.assert_called_once()
    if refresh_success:
        mock_execute_dialog.assert_awaited_once_with(mock_game_session_browser.return_value)
        mock_ensure_session_window.assert_awaited_once_with(
            default_online_interactions.network_client,
            mock_game_session_browser.return_value.joined_session.id,
            default_online_interactions.options,
        )
    else:
        mock_execute_dialog.assert_not_awaited()
        mock_ensure_session_window.assert_not_awaited()


@patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
async def test_host_game_session(mock_execute_dialog: AsyncMock, skip_qtbot, default_online_interactions, mocker):
    # Setup
    mock_ensure_session_window = AsyncMock(return_value=MagicMock())
    default_online_interactions.window_manager.ensure_multiplayer_session_window = mock_ensure_session_window
    default_online_interactions._ensure_logged_in = AsyncMock(return_value=True)
    mock_execute_dialog.return_value = QDialog.DialogCode.Accepted
    default_online_interactions.network_client.create_new_session = AsyncMock()

    # Run
    await default_online_interactions._host_game_session()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    default_online_interactions.network_client.create_new_session.assert_awaited_once_with("")
    mock_ensure_session_window.assert_awaited_once_with(
        default_online_interactions.network_client,
        default_online_interactions.network_client.create_new_session.return_value.id,
        default_online_interactions.options,
    )
