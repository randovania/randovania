from __future__ import annotations

import dataclasses
import datetime

from PySide6 import QtCore, QtWidgets

from randovania.gui.dialog.async_race_creation_dialog import AsyncRaceCreationDialog
from randovania.gui.dialog.async_race_settings_dialog import AsyncRaceSettingsDialog
from randovania.network_common.async_race_room import (
    AsyncRaceRoomEntry,
    AsyncRaceRoomRaceStatus,
    AsyncRaceRoomUserStatus,
    AsyncRaceSettings,
)
from randovania.network_common.game_details import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility


def test_validate(skip_qtbot):
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    dialog = AsyncRaceCreationDialog(parent)

    assert not dialog.button_group.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()

    dialog.ui.name_edit.setText("The Name")
    dialog.ui.start_time_edit.setDateTime(QtCore.QDateTime(2020, 1, 1, 0, 0, 0))
    dialog.ui.end_time_edit.setDateTime(QtCore.QDateTime(2021, 1, 1, 0, 0, 0))

    assert dialog.button_group.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()

    settings = AsyncRaceSettings(
        name="The Name",
        password=None,
        start_date=datetime.datetime(2020, 1, 1, 0, 0),
        end_date=datetime.datetime(2021, 1, 1, 0, 0),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        allow_pause=False,
    )
    assert dialog.create_settings_object() == settings

    dialog.ui.password_check.setChecked(True)
    assert not dialog.button_group.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()

    dialog.ui.password_edit.setText("The Secret")
    assert dialog.button_group.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()
    assert dialog.create_settings_object() == dataclasses.replace(settings, password="The Secret")


def test_settings_dialog(skip_qtbot) -> None:
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    dialog = AsyncRaceSettingsDialog(
        parent,
        AsyncRaceRoomEntry(
            id=1000,
            name="Async Room",
            has_password=False,
            creator="TheCreator",
            creation_date=datetime.datetime(2020, 1, 1),
            start_date=datetime.datetime(2020, 2, 1),
            end_date=datetime.datetime(2020, 3, 1),
            visibility=MultiplayerSessionVisibility.HIDDEN,
            race_status=AsyncRaceRoomRaceStatus.SCHEDULED,
            auth_token="Token",
            game_details=GameDetails(seed_hash="HASH", word_hash="Words Words", spoiler=False),
            presets_raw=[],
            is_admin=False,
            self_status=AsyncRaceRoomUserStatus.NOT_MEMBER,
            allow_pause=False,
        ),
    )

    assert dialog.create_settings_object() == AsyncRaceSettings(
        name="Async Room",
        password=None,
        start_date=datetime.datetime(2020, 2, 1, 0, 0),
        end_date=datetime.datetime(2020, 3, 1, 0, 0),
        visibility=MultiplayerSessionVisibility.HIDDEN,
        allow_pause=False,
    )
