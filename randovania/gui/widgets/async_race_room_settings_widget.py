import datetime

from PySide6 import QtCore, QtWidgets

from randovania.gui.generated.async_race_settings_ui import Ui_AsyncRaceRoomSettingsWidget
from randovania.gui.lib import common_qt_lib, signal_handling
from randovania.network_common.async_race_room import AsyncRaceSettings, race_uses_teams
from randovania.network_common.multiplayer_session import MAX_SESSION_NAME_LENGTH
from randovania.network_common.session_visibility import MultiplayerSessionVisibility


def _from_date(date: datetime.datetime) -> QtCore.QDateTime:
    return QtCore.QDateTime.fromSecsSinceEpoch(int(date.timestamp()))


def _to_date(date_time: QtCore.QDateTime) -> datetime.datetime:
    """
    The time edits are in the user's local time, but the network API always uses aware UTC datetimes.
    """
    result = date_time.toUTC().toPython()
    assert isinstance(result, datetime.datetime)
    return result.replace(tzinfo=datetime.UTC)


class AsyncRaceRoomSettingsWidget(QtWidgets.QWidget):
    ui: Ui_AsyncRaceRoomSettingsWidget

    Changed = QtCore.Signal(bool)

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.ui = Ui_AsyncRaceRoomSettingsWidget()
        self.ui.setupUi(self)

        self.ui.visibility_combo_box.setItemData(0, MultiplayerSessionVisibility.VISIBLE)
        self.ui.visibility_combo_box.setItemData(1, MultiplayerSessionVisibility.HIDDEN)

        self.ui.team_timer_combo_box.setItemData(0, True)
        self.ui.team_timer_combo_box.setItemData(1, False)

        self.ui.name_edit.setMaxLength(MAX_SESSION_NAME_LENGTH)
        signal_handling.on_checked(self.ui.password_check, self._on_password_check)

        self.ui.password_edit.setEnabled(False)
        self.ui.start_time_edit.setDateTime(_from_date(datetime.datetime.now()))
        self.ui.end_time_edit.setDateTime(_from_date(datetime.datetime.now() + datetime.timedelta(days=1)))

        self.ui.name_edit.textChanged.connect(self.validate)
        self.ui.password_edit.textChanged.connect(self.validate)
        self.ui.start_time_edit.dateTimeChanged.connect(self.validate)
        self.ui.end_time_edit.dateTimeChanged.connect(self.validate)
        self.ui.allow_coop_check.toggled.connect(self._update_team_timer_enabled)
        self.ui.allow_coop_check.toggled.connect(self.validate)

        self._world_count = 1
        self._multiworld_allowed = True
        self._update_team_timer_enabled()
        self.validate()

    @property
    def allow_coop(self) -> bool:
        return self.ui.allow_coop_check.isChecked()

    @property
    def shared_team_timer(self) -> bool:
        return bool(self.ui.team_timer_combo_box.currentData())

    @property
    def uses_teams(self) -> bool:
        """Whether the settings currently entered describe a race played in teams."""
        return race_uses_teams(self._world_count, self.allow_coop)

    def set_world_count(self, world_count: int) -> None:
        """Adjusts the team-related fields for the layout being raced."""
        self._world_count = world_count
        self._update_team_timer_enabled()

    def set_multiworld_allowed(self, allowed: bool) -> None:
        """
        Co-op and abandoning worlds both need a multiplayer session, so they can only be offered
        while every game being raced is one that supports multiworld.
        """
        self._multiworld_allowed = allowed
        tooltip = "" if allowed else "Not every game being raced supports being in a multiworld session"

        for check in (self.ui.allow_coop_check, self.ui.allow_abandon_worlds_check):
            if not allowed and check.isChecked():
                check.setChecked(False)
            check.setEnabled(allowed)
            check.setToolTip(tooltip)

        self._update_team_timer_enabled()

    def _update_team_timer_enabled(self) -> None:
        """How a team is timed only matters for a race that is actually played in teams."""
        uses_teams = self.uses_teams
        self.ui.team_timer_combo_box.setEnabled(uses_teams)
        self.ui.team_timer_label.setEnabled(uses_teams)
        self.ui.team_timer_combo_box.setToolTip(
            "" if uses_teams else "This race is played by individual players, so there is no team timer"
        )

    def create_settings_object(self) -> AsyncRaceSettings:
        """
        Prepares a settings object out of the configuration filled to the dialog.
        :return:
        """
        return AsyncRaceSettings(
            name=self.ui.name_edit.text(),
            password=self.ui.password_edit.text() if self.ui.password_edit.isEnabled() else None,
            start_date=_to_date(self.ui.start_time_edit.dateTime()),
            end_date=_to_date(self.ui.end_time_edit.dateTime()),
            visibility=self.ui.visibility_combo_box.currentData(),
            allow_pause=self.ui.allow_pause_check.isChecked(),
            allow_coop=self.ui.allow_coop_check.isChecked(),
            allow_abandon_worlds=self.ui.allow_abandon_worlds_check.isChecked(),
            shared_team_timer=self.shared_team_timer,
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
