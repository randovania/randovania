import datetime

from PySide6 import QtCore, QtWidgets

from randovania.gui.dialog.async_race_creation_dialog import AsyncRaceCreationDialog
from randovania.gui.lib import common_qt_lib, signal_handling
from randovania.network_common.async_race_room import AsyncRaceRoomEntry, AsyncRaceRoomRaceStatus, AsyncRaceSettings


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

    def create_settings_object(self) -> AsyncRaceSettings:
        """
        Prepares a settings object out of the configuration filled to the dialog.
        :return:
        """
        return AsyncRaceSettings(
            name=self.ui.name_edit.text(),
            password=self.ui.password_edit.text() if self.ui.password_edit.isEnabled() else None,
            start_date=self.ui.start_time_edit.dateTime().toPython(),
            end_date=self.ui.end_time_edit.dateTime().toPython(),
            visibility=self.ui.visibility_combo_box.currentData(),
            allow_pause=self.ui.allow_pause_check.isChecked(),
        )

    def _on_password_check(self, active: bool) -> None:
        """
        Called when password_check is toggled.
        """
        self.ui.password_edit.setEnabled(active)
        self.validate()

    def _validate_name(self) -> bool:
        """
        :return: True if name_edit is not empty
        """
        return len(self.ui.name_edit.text()) > 0

    def _validate_password(self) -> bool:
        """
        :return: True if password_check is unchecked or password_edit is not empty
        """
        return not self.ui.password_edit.isEnabled() or len(self.ui.password_edit.text()) > 0

    def _validate_end_time(self) -> bool:
        """
        :return: True is end_time_edit is after start_time_edit
        """
        return self.ui.end_time_edit.dateTime() > self.ui.start_time_edit.dateTime()

    def validate(self) -> None:
        """
        Validates all fields and enabled the confirm button.
        :return:
        """
        valid = True

        for widget, validator in [
            (self.ui.name_edit, self._validate_name),
            (self.ui.end_time_edit, self._validate_end_time),
            (self.ui.password_edit, self._validate_password),
        ]:
            widget_valid = validator()
            common_qt_lib.set_error_border_stylesheet(widget, not widget_valid)
            valid = valid and widget_valid

        self.button_group.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(valid)
