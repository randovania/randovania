from __future__ import annotations

import dataclasses
import datetime
from unittest.mock import MagicMock

from PySide6 import QtCore, QtWidgets

from randovania.gui.dialog.async_race_creation_dialog import AsyncRaceCreationDialog
from randovania.gui.dialog.async_race_settings_dialog import AsyncRaceSettingsDialog
from randovania.gui.lib.window_manager import WindowManager
from randovania.network_common.async_race_room import (
    AsyncRaceRoomEntry,
    AsyncRaceRoomRaceStatus,
    AsyncRaceRoomUserStatus,
    AsyncRaceSettings,
)
from randovania.network_common.game_details import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility


def test_validate(skip_qtbot, preset_manager, options):
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    window_manager = MagicMock(spec=WindowManager)
    window_manager.preset_manager = preset_manager
    dialog = AsyncRaceCreationDialog(parent, window_manager, options)

    assert not dialog.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()

    dialog.ui.settings_widget.ui.name_edit.setText("The Name")
    dialog.ui.settings_widget.ui.start_time_edit.setDateTime(QtCore.QDateTime(2020, 1, 1, 0, 0, 0))
    dialog.ui.settings_widget.ui.end_time_edit.setDateTime(QtCore.QDateTime(2021, 1, 1, 0, 0, 0))

    assert not dialog.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()
    dialog.selected_preset = MagicMock()
    dialog.ui.settings_widget.validate()
    assert dialog.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()

    settings = AsyncRaceSettings(
        name="The Name",
        password=None,
        start_date=datetime.datetime(2020, 1, 1, 0, 0),
        end_date=datetime.datetime(2021, 1, 1, 0, 0),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        allow_pause=False,
    )
    assert dialog.create_settings_object() == settings

    dialog.ui.settings_widget.ui.password_check.setChecked(True)
    assert not dialog.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()

    dialog.ui.settings_widget.ui.password_edit.setText("The Secret")
    assert dialog.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()
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
