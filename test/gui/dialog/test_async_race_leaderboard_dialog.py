from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.gui.dialog.async_race.async_race_leaderboard_dialog import AsyncRaceLeaderboardDialog
from randovania.network_common.async_race_room import RaceRoomLeaderboard, RaceRoomLeaderboardEntry
from randovania.network_common.user import RandovaniaUser

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def _cells(table: QtWidgets.QTableWidget) -> list[list[str]]:
    def text(row: int, column: int) -> str:
        item = table.item(row, column)
        assert item is not None
        return item.text()

    return [[text(row, column) for column in range(table.columnCount())] for row in range(table.rowCount())]


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
    data = _cells(dialog.table_widget)
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

    headers = [dialog.table_widget.horizontalHeaderItem(column) for column in range(dialog.table_widget.columnCount())]
    assert [header.text() for header in headers if header is not None] == ["Team", "Time", "Members"]

    data = _cells(dialog.table_widget)
    assert data == [
        ["The Winners", "1h 0min 0s", "A, B"],
        ["The Others", "Forfeited", "C"],
    ]
