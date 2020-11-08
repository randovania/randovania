import datetime

import pytest
from PySide2.QtWidgets import QDialog
from mock import patch, AsyncMock, MagicMock

from randovania.gui.online_game_list_window import GameSessionBrowserDialog
from randovania.network_client.game_session import GameSessionListEntry
from randovania.network_common.session_state import GameSessionState


@pytest.mark.asyncio
@patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
async def test_attempt_join(mock_execute_dialog: AsyncMock,
                            skip_qtbot):
    # Setup
    utc = datetime.timezone.utc
    mock_execute_dialog.return_value = QDialog.Accepted
    network_client = MagicMock()
    network_client.join_game_session = AsyncMock()
    session_a = GameSessionListEntry(id=1, name="A Game", has_password=True, state=GameSessionState.FINISHED,
                                     num_players=1, creator="You",
                                     creation_date=datetime.datetime(year=2015, month=5, day=1, tzinfo=utc))
    session_b = GameSessionListEntry(id=2, name="B Game", has_password=True, state=GameSessionState.IN_PROGRESS,
                                     num_players=1, creator="You",
                                     creation_date=datetime.datetime.now(utc) - datetime.timedelta(days=4))

    dialog = GameSessionBrowserDialog(network_client)
    dialog.sessions = [session_a, session_b]
    dialog.update_list()
    dialog.table_widget.selectRow(0)

    # Run
    await dialog.attempt_join()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    network_client.join_game_session.assert_awaited_once_with(session_b, "")
