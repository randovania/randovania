import datetime

from PySide6 import QtCore, QtWidgets

from randovania.gui.generated.async_race_settings_ui import Ui_AsyncRaceRoomSettingsWidget
from randovania.gui.lib import common_qt_lib, signal_handling
from randovania.network_common.async_race_room import AsyncRaceSettings
from randovania.network_common.multiplayer_session import MAX_SESSION_NAME_LENGTH
from randovania.network_common.session_visibility import MultiplayerSessionVisibility


def _from_date(date: datetime.datetime) -> QtCore.QDateTime:
    return QtCore.QDateTime.fromSecsSinceEpoch(int(date.timestamp()))


class AsyncRaceRoomSettingsWidget(QtWidgets.QWidget):
    ui: Ui_AsyncRaceRoomSettingsWidget

    Changed = QtCore.Signal(bool)

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.ui = Ui_AsyncRaceRoomSettingsWidget()
        self.ui.setupUi(self)

        self.ui.visibility_combo_box.setItemData(0, MultiplayerSessionVisibility.VISIBLE)
        self.ui.visibility_combo_box.setItemData(1, MultiplayerSessionVisibility.HIDDEN)

        self.ui.name_edit.setMaxLength(MAX_SESSION_NAME_LENGTH)
        signal_handling.on_checked(self.ui.password_check, self._on_password_check)

        self.ui.password_edit.setEnabled(False)
        self.ui.start_time_edit.setDateTime(_from_date(datetime.datetime.now()))
        self.ui.end_time_edit.setDateTime(_from_date(datetime.datetime.now() + datetime.timedelta(days=1)))

        self.ui.name_edit.textChanged.connect(self.validate)
        self.ui.password_edit.textChanged.connect(self.validate)
        self.ui.start_time_edit.dateTimeChanged.connect(self.validate)
        self.ui.end_time_edit.dateTimeChanged.connect(self.validate)

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
        return bool(self.ui.name_edit.text())

    def _validate_password(self) -> bool:
        """
        :return: True if password_check is unchecked or password_edit is not empty
        """
        return not self.ui.password_edit.isEnabled() or bool(self.ui.password_edit.text())

    def _validate_end_time(self) -> bool:
        """
        :return: True is end_time_edit is after start_time_edit
        """
        return self.ui.end_time_edit.dateTime() > self.ui.start_time_edit.dateTime()

    def validate(self) -> bool:
        """
        Validates all fields.
        :return: True if all fields are valid
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

        self.Changed.emit(valid)
        return valid
