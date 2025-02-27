from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.gui.dialog.async_race_leaderboard_dialog import AsyncRaceLeaderboardDialog
from randovania.network_common.async_race_room import RaceRoomLeaderboard, RaceRoomLeaderboardEntry
from randovania.network_common.user import RandovaniaUser

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_create_widget(skip_qtbot: QtBot):
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    dialog = AsyncRaceLeaderboardDialog(
        parent,
        RaceRoomLeaderboard(
            [
                RaceRoomLeaderboardEntry(RandovaniaUser(0, "A"), datetime.timedelta(hours=1)),
                RaceRoomLeaderboardEntry(RandovaniaUser(1, "B"), datetime.timedelta(hours=2)),
                RaceRoomLeaderboardEntry(RandovaniaUser(2, "C"), None),
            ]
        ),
    )

    data = [
        [dialog.table_widget.item(row, column).text() for column in range(dialog.table_widget.columnCount())]
        for row in range(dialog.table_widget.rowCount())
    ]
    assert data == [
        ["A", "1h 0min 0s"],
        ["B", "2h 0min 0s"],
        ["C", "Forfeited"],
    ]
