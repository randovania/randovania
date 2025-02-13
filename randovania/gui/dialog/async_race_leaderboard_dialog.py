from PySide6 import QtCore, QtWidgets

from randovania.network_common.async_race_room import RaceRoomLeaderboard


class AsyncRaceLeaderboardDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget, leaderboard: RaceRoomLeaderboard):
        super().__init__(parent)
        self.setWindowTitle("Leaderboard")

        self.root_layout = QtWidgets.QGridLayout(self)

        self.table_widget = QtWidgets.QTableWidget(self)
        self.table_widget.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["User", "Time"])
        self.table_widget.setRowCount(len(leaderboard.entries))
        self.root_layout.addWidget(self.table_widget)

        for row, entry in enumerate(leaderboard.entries):
            self.table_widget.setItem(row, 0, QtWidgets.QTableWidgetItem(entry.user.name))
            time_widget = QtWidgets.QTableWidgetItem()

            if entry.time is None:
                value = "Forfeited"
            else:
                seconds = int(entry.time.total_seconds())
                minutes, seconds = seconds // 60, seconds % 60
                hours, minutes = minutes // 60, minutes % 60

                value = f"{hours}h {minutes}min {seconds}s"

            time_widget.setData(QtCore.Qt.ItemDataRole.DisplayRole, value)
            self.table_widget.setItem(row, 1, time_widget)
