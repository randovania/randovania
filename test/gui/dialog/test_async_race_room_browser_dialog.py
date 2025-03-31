from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock, call

import pytest
from PySide6 import QtCore

from randovania.game.game_enum import RandovaniaGame
from randovania.gui.dialog.async_race_room_browser_dialog import AsyncRaceRoomBrowserDialog
from randovania.network_common import error
from randovania.network_common.async_race_room import AsyncRaceRoomListEntry, AsyncRaceRoomRaceStatus
from randovania.network_common.session_visibility import MultiplayerSessionVisibility

if TYPE_CHECKING:
    import pytest_mock
    from pytestqt.qtbot import QtBot


@pytest.fixture(name="sessions")
def create_sessions() -> list[AsyncRaceRoomListEntry]:
    utc = datetime.UTC
    session_a = AsyncRaceRoomListEntry(
        id=1,
        name="A Game",
        games=[RandovaniaGame.BLANK],
        has_password=False,
        creator="You",
        creation_date=datetime.datetime.now(utc) - datetime.timedelta(days=4),
        start_date=datetime.datetime.now(utc) - datetime.timedelta(days=3),
        end_date=datetime.datetime.now(utc) - datetime.timedelta(days=2),
        visibility=MultiplayerSessionVisibility.HIDDEN,
        race_status=AsyncRaceRoomRaceStatus.FINISHED,
    )
    session_b = AsyncRaceRoomListEntry(
        id=2,
        name="B Game",
        games=[RandovaniaGame.BLANK],
        has_password=True,
        creator="You",
        creation_date=datetime.datetime.now(utc) - datetime.timedelta(days=8),
        start_date=datetime.datetime.now(utc) - datetime.timedelta(days=1),
        end_date=datetime.datetime.now(utc) + datetime.timedelta(days=2),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        race_status=AsyncRaceRoomRaceStatus.ACTIVE,
    )

    session_c = AsyncRaceRoomListEntry(
        id=3,
        name="C Game",
        games=[RandovaniaGame.BLANK],
        has_password=True,
        creator="You",
        creation_date=datetime.datetime.now(utc) - datetime.timedelta(days=4),
        start_date=datetime.datetime.now(utc) + datetime.timedelta(days=3),
        end_date=datetime.datetime.now(utc) + datetime.timedelta(days=4),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        race_status=AsyncRaceRoomRaceStatus.SCHEDULED,
    )
    return [session_a, session_b, session_c]


async def test_attempt_join(
    sessions: list[AsyncRaceRoomListEntry], skip_qtbot: QtBot, mocker: pytest_mock.MockFixture
) -> None:
    # Setup
    mock_prompt = mocker.patch("randovania.gui.dialog.text_prompt_dialog.TextPromptDialog.prompt", autospec=True)
    joined_session = MagicMock()

    network_client = MagicMock()
    network_client.get_async_race_room = AsyncMock(
        side_effect=[
            error.WrongPasswordError,
            joined_session,
        ]
    )

    dialog = AsyncRaceRoomBrowserDialog(network_client)
    skip_qtbot.addWidget(dialog)
    dialog.sessions = sessions
    dialog.update_list()
    dialog.table_widget.selectRow(0)

    # Run
    await dialog._attempt_join()

    # Assert
    mock_prompt.assert_awaited_once_with(
        title=ANY,
        description=ANY,
        is_password=True,
    )
    network_client.get_async_race_room.assert_has_awaits(
        [
            call(2, None),
            call(2, mock_prompt.return_value),
        ]
    )
    assert dialog.joined_session is joined_session


def test_filter(sessions: list[AsyncRaceRoomListEntry], skip_qtbot: QtBot) -> None:
    def click_helper(qt_object):
        skip_qtbot.mouseClick(qt_object, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(2, qt_object.height() / 2))

    # Setup
    network_client = MagicMock()

    dialog = AsyncRaceRoomBrowserDialog(network_client)
    skip_qtbot.addWidget(dialog)
    dialog.sessions = sessions
    dialog.update_list()

    # default = no Finished visible
    assert len(dialog.visible_sessions) == 2

    # make all visible
    click_helper(dialog.state_hidden_check)
    assert len(dialog.visible_sessions) == 3

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
