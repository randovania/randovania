from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from PySide6 import QtCore

from randovania.gui.dialog.multiplayer_session_browser_dialog import MultiplayerSessionBrowserDialog
from randovania.network_common.multiplayer_session import MultiplayerSessionListEntry
from randovania.network_common.session_visibility import MultiplayerSessionVisibility


@pytest.fixture(name="sessions")
def create_sessions():
    utc = datetime.UTC
    session_a = MultiplayerSessionListEntry(
        id=1,
        name="A Game",
        has_password=False,
        visibility=MultiplayerSessionVisibility.HIDDEN,
        num_users=1,
        num_worlds=3,
        creator="You",
        is_user_in_session=True,
        creation_date=datetime.datetime.now(utc) - datetime.timedelta(days=4),
        join_date=datetime.datetime(year=2016, month=5, day=1, tzinfo=utc),
    )
    session_b = MultiplayerSessionListEntry(
        id=2,
        name="B Game",
        has_password=True,
        visibility=MultiplayerSessionVisibility.VISIBLE,
        num_users=2,
        num_worlds=2,
        creator="You",
        is_user_in_session=False,
        creation_date=datetime.datetime.now(utc) - datetime.timedelta(days=8),
        join_date=datetime.datetime(year=2016, month=5, day=1, tzinfo=utc),
    )

    session_c = MultiplayerSessionListEntry(
        id=3,
        name="C Game",
        has_password=True,
        visibility=MultiplayerSessionVisibility.VISIBLE,
        num_users=2,
        num_worlds=0,
        creator="You",
        is_user_in_session=False,
        creation_date=datetime.datetime.now(utc) - datetime.timedelta(days=4),
        join_date=datetime.datetime(year=2016, month=5, day=1, tzinfo=utc),
    )
    return [session_a, session_b, session_c]


async def test_attempt_join(sessions, skip_qtbot):
    # Setup
    network_client = MagicMock()
    network_client.attempt_join_with_password_check = AsyncMock()

    dialog = MultiplayerSessionBrowserDialog(network_client)
    dialog.sessions = sessions
    dialog.update_list()
    dialog.table_widget.selectRow(0)

    # Run
    await dialog._attempt_join()

    # Assert
    network_client.attempt_join_with_password_check.assert_awaited_once_with(sessions[1])


def test_filter(sessions, skip_qtbot):
    # still don't ask me why I need to explicity use the middle (height / 2) to click some of the boxes
    def click_helper(qt_object):
        skip_qtbot.mouseClick(qt_object, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(2, qt_object.height() / 2))

    # Setup
    network_client = MagicMock()

    dialog = MultiplayerSessionBrowserDialog(network_client)
    dialog.sessions = sessions
    dialog.update_list()

    # default = no Finished visible
    assert len(dialog.visible_sessions) == 2

    # make all visible
    click_helper(dialog.state_hidden_check)
    assert len(dialog.visible_sessions) == 3

    # only show where you are member
    click_helper(dialog.is_member_no_check)
    assert len(dialog.visible_sessions) == 1
    assert dialog.visible_sessions[0].id == 1
    # set back
    click_helper(dialog.is_member_no_check)

    # only show session with password
    click_helper(dialog.has_password_no_check)
    assert len(dialog.visible_sessions) == 2
    assert dialog.visible_sessions[0].id == 2
    assert dialog.visible_sessions[1].id == 3
    # set back
    click_helper(dialog.has_password_no_check)

    # filter by age
    dialog.filter_age_spin.setValue(5)
    dialog.update_list()
    assert len(dialog.visible_sessions) == 2
    assert dialog.visible_sessions[0].id == 1
    assert dialog.visible_sessions[1].id == 3
