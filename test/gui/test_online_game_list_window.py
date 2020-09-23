import pytest
from PySide2.QtWidgets import QDialog
from mock import patch, AsyncMock, MagicMock

from randovania.gui.online_game_list_window import GameSessionBrowserDialog


@pytest.mark.asyncio
@patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
async def test_attempt_join(mock_execute_dialog: AsyncMock,
                            skip_qtbot):
    # Setup
    mock_execute_dialog.return_value = QDialog.Accepted
    network_client = MagicMock()
    network_client.join_game_session = AsyncMock()
    session = MagicMock()

    dialog = GameSessionBrowserDialog(network_client)
    dialog.sessions = [session]
    dialog.update_list()
    dialog.table_widget.selectRow(0)

    # Run
    await dialog.attempt_join()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    network_client.join_game_session.assert_awaited_once_with(session, "")
