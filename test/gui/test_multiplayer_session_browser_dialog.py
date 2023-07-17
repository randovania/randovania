from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

from randovania.gui.dialog.multiplayer_session_browser_dialog import MultiplayerSessionBrowserDialog
from randovania.network_common.multiplayer_session import MultiplayerSessionListEntry
from randovania.network_common.session_state import MultiplayerSessionState


async def test_attempt_join(skip_qtbot):
    # Setup
    utc = datetime.UTC
    network_client = MagicMock()
    network_client.attempt_join_with_password_check = AsyncMock()

    session_a = MultiplayerSessionListEntry(
        id=1, name="A Game", has_password=True, state=MultiplayerSessionState.FINISHED,
        num_users=1, num_worlds=0, creator="You", is_user_in_session=True,
        creation_date=datetime.datetime(year=2015, month=5, day=1, tzinfo=utc),
        join_date=datetime.datetime(year=2016, month=5, day=1, tzinfo=utc),
    )
    session_b = MultiplayerSessionListEntry(
        id=2, name="B Game", has_password=True,
        state=MultiplayerSessionState.IN_PROGRESS,
        num_users=1, num_worlds=0, creator="You", is_user_in_session=True,
        creation_date=datetime.datetime.now(utc) - datetime.timedelta(days=4),
        join_date=datetime.datetime(year=2016, month=5, day=1, tzinfo=utc),
    )

    dialog = MultiplayerSessionBrowserDialog(network_client)
    dialog.sessions = [session_a, session_b]
    dialog.update_list()
    dialog.table_widget.selectRow(0)

    # Run
    await dialog._attempt_join()

    # Assert
    network_client.attempt_join_with_password_check.assert_awaited_once_with(session_b)
