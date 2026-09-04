from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from PySide6 import QtCore, QtWidgets

from randovania.game.game_enum import RandovaniaGame
from randovania.gui.dialog.async_race.async_race_creation_dialog import AsyncRaceCreationDialog
from randovania.gui.dialog.async_race.async_race_settings_dialog import AsyncRaceSettingsDialog
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
    await dialog._on_select_preset(replace_row=None)
    assert dialog.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()
    assert dialog.world_count == 1

    settings = AsyncRaceSettings(
        name="The Name",
        password=None,
        start_date=QtCore.QDateTime(2020, 1, 1, 0, 0, 0).toUTC().toPython().replace(tzinfo=datetime.UTC),
        end_date=QtCore.QDateTime(2021, 1, 1, 0, 0, 0).toUTC().toPython().replace(tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        allow_pause=False,
    )
    assert dialog.create_settings_object() == settings

    dialog.ui.settings_widget.ui.password_check.setChecked(True)
    assert not dialog.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()

    dialog.ui.settings_widget.ui.password_edit.setText("The Secret")
    assert dialog.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()
    assert dialog.create_settings_object() == settings.model_copy(update={"password": "The Secret"})


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
    dialog.generate_layout_from_presets = AsyncMock()
    if not success:
        dialog.generate_layout_from_presets.return_value = None

    dialog.selected_presets = [MagicMock()] if has_preset else []

    # Run
    await dialog._generate_and_accept()

    # Assert
    if has_preset:
        dialog.generate_layout_from_presets.assert_awaited_once_with(dialog.selected_presets, spoiler=True)
        dialog.result()
    else:
        dialog.generate_layout_from_presets.assert_not_called()

    assert dialog.result() == (
        QtWidgets.QDialog.DialogCode.Accepted if success else QtWidgets.QDialog.DialogCode.Rejected
    )


async def test_add_change_and_remove_worlds(skip_qtbot, preset_manager, options, mocker: pytest_mock.MockFixture):
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    window_manager = MagicMock(spec=WindowManager)
    window_manager.preset_manager = preset_manager
    dialog = AsyncRaceCreationDialog(parent, window_manager, options)

    blank = preset_manager.default_preset_for_game(RandovaniaGame.BLANK)
    dread = preset_manager.default_preset_for_game(RandovaniaGame.METROID_DREAD)
    to_select = [blank, blank, dread]

    async def execute_dialog_effect(diag: SelectPresetDialog) -> QtWidgets.QDialog.DialogCode:
        preset = to_select.pop(0)
        signal_handling.set_combo_with_value(diag.game_selection_combo, preset.game)
        diag.select_preset_widget.create_preset_tree.select_preset(preset)
        return QtWidgets.QDialog.DialogCode.Accepted

    mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog",
        autospec=True,
        side_effect=execute_dialog_effect,
    )

    # A single world is played by individuals, so there is no team timer to pick
    await dialog._on_select_preset(replace_row=None)
    assert not dialog._uses_teams()
    assert not dialog.ui.settings_widget.ui.team_timer_combo_box.isEnabled()

    # A second one makes it a multiworld, played in teams of whatever size the organiser wants
    await dialog._on_select_preset(replace_row=None)
    assert dialog.world_count == 2
    assert dialog._uses_teams()
    assert dialog.ui.settings_widget.ui.team_timer_combo_box.isEnabled()

    # Replacing a world keeps the count, changing only that entry
    dialog.ui.world_list.setCurrentRow(1)
    await dialog._on_select_preset(replace_row=1)
    assert [preset.game for preset in dialog.selected_presets] == [
        RandovaniaGame.BLANK,
        RandovaniaGame.METROID_DREAD,
    ]
    assert dialog.ui.world_list.count() == 2

    # And removing one goes back to a single world
    dialog._on_remove_world()
    assert dialog.world_count == 1
    assert not dialog._uses_teams()


async def test_multiworld_rejects_game_without_session_support(
    skip_qtbot, preset_manager, options, mocker: pytest_mock.MockFixture
):
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    window_manager = MagicMock(spec=WindowManager)
    window_manager.preset_manager = preset_manager
    dialog = AsyncRaceCreationDialog(parent, window_manager, options)

    dialog.ui.settings_widget.ui.name_edit.setText("The Name")
    dialog.ui.settings_widget.ui.start_time_edit.setDateTime(QtCore.QDateTime(2020, 1, 1, 0, 0, 0))
    dialog.ui.settings_widget.ui.end_time_edit.setDateTime(QtCore.QDateTime(2021, 1, 1, 0, 0, 0))

    unsupported = next(
        game
        for game in RandovaniaGame.sorted_all_games()
        if game.data.development_state.can_view() and not game.data.defaults_available_in_game_sessions
    )
    dialog.selected_presets = [preset_manager.default_preset_for_game(unsupported)] * 2
    dialog._update_world_list()

    assert dialog._multiworld_messages()
    assert not dialog.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()
    assert unsupported not in dialog._allowed_games(uses_teams=True)
    assert unsupported in dialog._allowed_games(uses_teams=False)


async def test_first_world_without_multiworld_locks_the_room_down(
    skip_qtbot, preset_manager, options, mocker: pytest_mock.MockFixture
):
    """
    Worlds are added one at a time, so a first world multiworld can't host settles the room:
    no second world may be added, and neither co-op nor abandoning worlds stay available.
    """
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    window_manager = MagicMock(spec=WindowManager)
    window_manager.preset_manager = preset_manager
    dialog = AsyncRaceCreationDialog(parent, window_manager, options)
    settings = dialog.ui.settings_widget

    unsupported = next(
        game
        for game in RandovaniaGame.sorted_all_games()
        if game.data.development_state.can_view() and not game.data.defaults_available_in_game_sessions
    )

    # The organiser turns both on before picking anything
    settings.ui.allow_coop_check.setChecked(True)
    settings.ui.allow_abandon_worlds_check.setChecked(True)
    assert settings.allow_coop

    # Adding a world multiworld can't host takes them away again
    dialog.selected_presets = [preset_manager.default_preset_for_game(unsupported)]
    dialog._update_world_list()

    assert not dialog._worlds_allow_multiworld
    assert not dialog.ui.preset_button.isEnabled()
    assert dialog.ui.preset_button.toolTip()

    for check in (settings.ui.allow_coop_check, settings.ui.allow_abandon_worlds_check):
        assert not check.isEnabled()
        assert not check.isChecked()

    # Which leaves a plain solo race, and nothing objectionable to report
    assert not dialog._uses_teams()
    assert dialog._multiworld_messages() == []

    # Removing that world opens everything back up
    dialog.ui.world_list.setCurrentRow(0)
    dialog._on_remove_world()

    assert dialog.ui.preset_button.isEnabled()
    assert settings.ui.allow_coop_check.isEnabled()
    assert settings.ui.allow_abandon_worlds_check.isEnabled()


async def test_multiworld_capable_first_world_keeps_add_available(
    skip_qtbot, preset_manager, options, mocker: pytest_mock.MockFixture
):
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    window_manager = MagicMock(spec=WindowManager)
    window_manager.preset_manager = preset_manager
    dialog = AsyncRaceCreationDialog(parent, window_manager, options)

    dialog.selected_presets = [preset_manager.default_preset_for_game(RandovaniaGame.BLANK)]
    dialog._update_world_list()

    assert dialog._worlds_allow_multiworld
    assert dialog.ui.preset_button.isEnabled()
    assert dialog.ui.settings_widget.ui.allow_coop_check.isEnabled()
    assert dialog.ui.settings_widget.ui.allow_abandon_worlds_check.isEnabled()


def test_settings_dialog(skip_qtbot) -> None:
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    dialog = AsyncRaceSettingsDialog(
        parent,
        AsyncRaceRoomEntry(
            id=1000,
            name="Async Room",
            creator="TheCreator",
            creation_date=datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            start_date=datetime.datetime(2020, 2, 1, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2020, 3, 1, tzinfo=datetime.UTC),
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
        start_date=datetime.datetime(2020, 2, 1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2020, 3, 1, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.HIDDEN,
        allow_pause=False,
    )
