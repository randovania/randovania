import datetime

from PySide6 import QtCore, QtWidgets

from randovania.gui.dialog.async_race_creation_dialog import AsyncRaceCreationDialog
from randovania.gui.lib import signal_handling
from randovania.network_common.async_race_room import AsyncRaceRoomEntry, AsyncRaceRoomRaceStatus


def _from_date(date: datetime.datetime) -> QtCore.QDateTime:
    return QtCore.QDateTime.fromSecsSinceEpoch(int(date.timestamp()))


class AsyncRaceSettingsDialog(AsyncRaceCreationDialog):
    def __init__(self, parent: QtWidgets.QWidget, current_room: AsyncRaceRoomEntry):
        super().__init__(parent)

        self.room = current_room

        self.ui.name_edit.setText(self.room.name)
        self.ui.password_edit.setVisible(False)
        self.ui.password_check.setVisible(False)
        self.ui.start_time_edit.setDateTime(QtCore.QDateTime.fromSecsSinceEpoch(int(self.room.start_date.timestamp())))
        self.ui.end_time_edit.setDateTime(QtCore.QDateTime.fromSecsSinceEpoch(int(self.room.end_date.timestamp())))
        self.ui.allow_pause_check.setChecked(self.room.allow_pause)

        if self.room.race_status != AsyncRaceRoomRaceStatus.SCHEDULED:
            self.ui.start_time_edit.setEnabled(False)
            self.ui.start_time_edit.setToolTip("Race already started")

            if self.room.allow_pause:
                self.ui.allow_pause_check.setEnabled(False)
                self.ui.allow_pause_check.setToolTip("Unable to disallow pausing of started races")

        self.ui.end_time_edit.setEnabled(self.room.race_status != AsyncRaceRoomRaceStatus.FINISHED)

        signal_handling.set_combo_with_value(self.ui.visibility_combo_box, self.room.visibility)

        self.validate()
