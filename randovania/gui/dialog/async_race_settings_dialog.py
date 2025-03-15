import datetime

from PySide6 import QtCore, QtWidgets

from randovania.gui.lib import signal_handling
from randovania.gui.widgets.async_race_room_settings_widget import AsyncRaceRoomSettingsWidget
from randovania.network_common.async_race_room import AsyncRaceRoomEntry, AsyncRaceRoomRaceStatus, AsyncRaceSettings


def _from_date(date: datetime.datetime) -> QtCore.QDateTime:
    return QtCore.QDateTime.fromSecsSinceEpoch(int(date.timestamp()))


class AsyncRaceSettingsDialog(QtWidgets.QDialog):
    settings_widget: AsyncRaceRoomSettingsWidget

    def __init__(self, parent: QtWidgets.QWidget, current_room: AsyncRaceRoomEntry):
        super().__init__(parent)

        self.room = current_room

        self.setWindowTitle("Async Race Room Settings")
        self.resize(362, 162)
        self.root_layout = QtWidgets.QVBoxLayout(self)

        self.settings_widget = AsyncRaceRoomSettingsWidget(self)
        self.root_layout.addWidget(self.settings_widget)

        self.button_group = QtWidgets.QDialogButtonBox(self)
        self.button_group.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel | QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        self.root_layout.addWidget(self.button_group)

        self.button_group.accepted.connect(self.accept)
        self.button_group.rejected.connect(self.reject)
        self.settings_widget.Changed.connect(self._post_validate)

        self.settings_widget.ui.name_edit.setText(self.room.name)
        self.settings_widget.ui.password_edit.setVisible(False)
        self.settings_widget.ui.password_check.setVisible(False)
        self.settings_widget.ui.start_time_edit.setDateTime(
            QtCore.QDateTime.fromSecsSinceEpoch(int(self.room.start_date.timestamp()))
        )
        self.settings_widget.ui.end_time_edit.setDateTime(
            QtCore.QDateTime.fromSecsSinceEpoch(int(self.room.end_date.timestamp()))
        )
        self.settings_widget.ui.allow_pause_check.setChecked(self.room.allow_pause)

        if self.room.race_status != AsyncRaceRoomRaceStatus.SCHEDULED:
            self.settings_widget.ui.start_time_edit.setEnabled(False)
            self.settings_widget.ui.start_time_edit.setToolTip("Race already started")

            if self.room.allow_pause:
                self.settings_widget.ui.allow_pause_check.setEnabled(False)
                self.settings_widget.ui.allow_pause_check.setToolTip("Unable to disallow pausing of started races")

        self.settings_widget.ui.end_time_edit.setEnabled(self.room.race_status != AsyncRaceRoomRaceStatus.FINISHED)

        signal_handling.set_combo_with_value(self.settings_widget.ui.visibility_combo_box, self.room.visibility)
        self.settings_widget.validate()

    def create_settings_object(self) -> AsyncRaceSettings:
        return self.settings_widget.create_settings_object()

    def _post_validate(self, valid: bool) -> None:
        self.button_group.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(valid)
