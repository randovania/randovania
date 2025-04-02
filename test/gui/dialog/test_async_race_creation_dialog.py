from __future__ import annotations

import dataclasses
import datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from PySide6 import QtCore, QtWidgets

from randovania.game.game_enum import RandovaniaGame
from randovania.gui.dialog.async_race_creation_dialog import AsyncRaceCreationDialog
from randovania.gui.dialog.async_race_settings_dialog import AsyncRaceSettingsDialog
from randovania.gui.lib import signal_handling
from randovania.gui.lib.window_manager import WindowManager
from randovania.network_common.async_race_room import (
    AsyncRaceRoomEntry,
    AsyncRaceRoomRaceStatus,
    AsyncRaceRoomUserStatus,
    AsyncRaceSettings,
)
from randovania.network_common.game_details import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility

if TYPE_CHECKING:
    import pytest_mock

    from randovania.gui.dialog.select_preset_dialog import SelectPresetDialog


async def test_validate(skip_qtbot, preset_manager, options, mocker: pytest_mock.MockFixture):
    mocker.patch("randovania.is_dev_version", return_value=True)

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

    async def execute_dialog_effect(diag: SelectPresetDialog) -> QtWidgets.QDialog.DialogCode:
        signal_handling.set_combo_with_value(diag.game_selection_combo, RandovaniaGame.BLANK)
        diag.select_preset_widget.create_preset_tree.select_preset(
            preset_manager.default_preset_for_game(RandovaniaGame.BLANK)
        )
        return QtWidgets.QDialog.DialogCode.Accepted

    mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog",
        autospec=True,
        side_effect=execute_dialog_effect,
    )
    await dialog._on_select_preset()
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


@pytest.mark.parametrize(
    ("has_preset", "success"),
    [
        (False, False),
        (True, False),
        (True, True),
    ],
)
async def test_generate_and_accept(skip_qtbot, preset_manager, options, has_preset: bool, success: bool):
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    window_manager = MagicMock(spec=WindowManager)
    window_manager.preset_manager = preset_manager
    dialog = AsyncRaceCreationDialog(parent, window_manager, options)
    dialog.generate_layout_from_preset = AsyncMock()
    if not success:
        dialog.generate_layout_from_preset.return_value = None

    dialog.selected_preset = MagicMock() if has_preset else None

    # Run
    await dialog._generate_and_accept()

    # Assert
    if has_preset:
        dialog.generate_layout_from_preset.assert_awaited_once_with(preset=dialog.selected_preset, spoiler=True)
        dialog.result()
    else:
        dialog.generate_layout_from_preset.assert_not_called()

    assert dialog.result() == (
        QtWidgets.QDialog.DialogCode.Accepted if success else QtWidgets.QDialog.DialogCode.Rejected
    )


def test_settings_dialog(skip_qtbot) -> None:
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    dialog = AsyncRaceSettingsDialog(
        parent,
        AsyncRaceRoomEntry(
            id=1000,
            name="Async Room",
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
