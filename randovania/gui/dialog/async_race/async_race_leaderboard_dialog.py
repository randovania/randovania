from PySide6 import QtCore, QtWidgets

from randovania.gui.lib.time_lib import format_elapsed_time
from randovania.network_common.async_race_room import RaceRoomLeaderboard


class AsyncRaceLeaderboardDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget, leaderboard: RaceRoomLeaderboard) -> None:
        super().__init__(parent)
        self.setWindowTitle("Leaderboard")

        self.root_layout = QtWidgets.QGridLayout(self)

        has_teams = leaderboard.uses_teams

        self.table_widget = QtWidgets.QTableWidget(self)
        self.table_widget.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setColumnCount(3 if has_teams else 2)
        self.table_widget.setHorizontalHeaderLabels(["Team", "Time", "Members"] if has_teams else ["User", "Time"])
        self.table_widget.setRowCount(len(leaderboard.entries))
        self.root_layout.addWidget(self.table_widget)

        for row, entry in enumerate(leaderboard.entries):
            self.table_widget.setItem(row, 0, QtWidgets.QTableWidgetItem(entry.display_name))
            if has_teams:
                members = ", ".join(member.name for member in entry.members)
                self.table_widget.setItem(row, 2, QtWidgets.QTableWidgetItem(members))
            time_widget = QtWidgets.QTableWidgetItem()

            if entry.time is None:
                value = "Forfeited"
            else:
                value = format_elapsed_time(entry.time)

            time_widget.setData(QtCore.Qt.ItemDataRole.DisplayRole, value)
            self.table_widget.setItem(row, 1, time_widget)
