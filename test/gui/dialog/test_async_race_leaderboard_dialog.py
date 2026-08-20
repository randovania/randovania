from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.gui.dialog.async_race.async_race_leaderboard_dialog import AsyncRaceLeaderboardDialog
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
            entries=[
                RaceRoomLeaderboardEntry(
                    display_name="A", time=datetime.timedelta(hours=1), members=[RandovaniaUser(0, "A")]
                ),
                RaceRoomLeaderboardEntry(
                    display_name="B", time=datetime.timedelta(hours=2), members=[RandovaniaUser(1, "B")]
                ),
                RaceRoomLeaderboardEntry(display_name="C", time=None, members=[RandovaniaUser(2, "C")]),
            ]
        ),
    )

    assert dialog.table_widget.columnCount() == 2
    data = [
        [dialog.table_widget.item(row, column).text() for column in range(dialog.table_widget.columnCount())]
        for row in range(dialog.table_widget.rowCount())
    ]
    assert data == [
        ["A", "1h 0min 0s"],
        ["B", "2h 0min 0s"],
        ["C", "Forfeited"],
    ]


def test_create_widget_with_teams(skip_qtbot: QtBot):
    """A room played in teams is scored by team, with a column listing who was on each."""
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    dialog = AsyncRaceLeaderboardDialog(
        parent,
        RaceRoomLeaderboard(
            entries=[
                RaceRoomLeaderboardEntry(
                    display_name="The Winners",
                    time=datetime.timedelta(hours=1),
                    members=[RandovaniaUser(0, "A"), RandovaniaUser(1, "B")],
                ),
                RaceRoomLeaderboardEntry(display_name="The Others", time=None, members=[RandovaniaUser(2, "C")]),
            ],
            uses_teams=True,
        ),
    )

    assert [
        dialog.table_widget.horizontalHeaderItem(column).text() for column in range(dialog.table_widget.columnCount())
    ] == ["Team", "Time", "Members"]

    data = [
        [dialog.table_widget.item(row, column).text() for column in range(dialog.table_widget.columnCount())]
        for row in range(dialog.table_widget.rowCount())
    ]
    assert data == [
        ["The Winners", "1h 0min 0s", "A, B"],
        ["The Others", "Forfeited", "C"],
    ]
