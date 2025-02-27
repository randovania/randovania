from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from PySide6 import QtWidgets

from randovania.gui.async_race_room_window import AsyncRaceRoomWindow
from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common.async_race_room import (
    AsyncRaceRoomEntry,
    AsyncRaceRoomRaceStatus,
    AsyncRaceRoomUserStatus,
)
from randovania.network_common.game_details import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility

if TYPE_CHECKING:
    import pytest_mock
    from pytestqt.qtbot import QtBot

    from randovania.layout.preset import Preset


def create_room(
    preset: Preset,
    self_status: AsyncRaceRoomUserStatus = AsyncRaceRoomUserStatus.NOT_MEMBER,
    race_status: AsyncRaceRoomRaceStatus = AsyncRaceRoomRaceStatus.ACTIVE,
    allow_pause: bool = False,
    is_admin: bool = False,
) -> AsyncRaceRoomEntry:
    return AsyncRaceRoomEntry(
        id=1000,
        name="Async Room",
        has_password=False,
        creator="TheCreator",
        creation_date=datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
        start_date=datetime.datetime(2020, 2, 1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2020, 3, 1, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        race_status=race_status,
        auth_token="Token",
        game_details=GameDetails(seed_hash="HASH", word_hash="Words Words", spoiler=False),
        presets_raw=[VersionedPreset.with_preset(preset).as_bytes()],
        is_admin=is_admin,
        self_status=self_status,
        allow_pause=allow_pause,
    )


def create_window(skip_qtbot: QtBot, room: AsyncRaceRoomEntry) -> AsyncRaceRoomWindow:
    window = AsyncRaceRoomWindow(room, MagicMock(spec=QtNetworkClient), MagicMock(), MagicMock())
    skip_qtbot.add_widget(window)
    return window


async def button_state_helper(
    window: AsyncRaceRoomWindow, after: AsyncRaceRoomUserStatus | None, button: QtWidgets.QPushButton, method
) -> None:
    window._status_transition = AsyncMock()

    if after is None:
        assert not button.isEnabled()
    else:
        assert button.isEnabled()
        await method()
        window._status_transition.assert_awaited_once_with(after)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (AsyncRaceRoomUserStatus.NOT_MEMBER, None),
        (AsyncRaceRoomUserStatus.JOINED, AsyncRaceRoomUserStatus.STARTED),
        (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.JOINED),
    ],
)
async def test_on_start(skip_qtbot, default_blank_preset, before, after):
    window = create_window(skip_qtbot, create_room(default_blank_preset, self_status=before))
    await button_state_helper(window, after, window.ui.start_button, window._on_start)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (AsyncRaceRoomUserStatus.JOINED, None),
        (AsyncRaceRoomUserStatus.PAUSED, AsyncRaceRoomUserStatus.STARTED),
        (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.PAUSED),
        (AsyncRaceRoomUserStatus.FINISHED, None),
    ],
)
async def test_on_pause(skip_qtbot, default_blank_preset, before, after):
    window = create_window(skip_qtbot, create_room(default_blank_preset, self_status=before))
    await button_state_helper(window, after, window.ui.pause_button, window._on_pause)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (AsyncRaceRoomUserStatus.JOINED, None),
        (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.FINISHED),
        (AsyncRaceRoomUserStatus.FINISHED, AsyncRaceRoomUserStatus.STARTED),
        (AsyncRaceRoomUserStatus.FORFEITED, None),
    ],
)
async def test_on_finish(skip_qtbot, default_blank_preset, before, after):
    window = create_window(skip_qtbot, create_room(default_blank_preset, self_status=before))
    await button_state_helper(window, after, window.ui.finish_button, window._on_finish)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (AsyncRaceRoomUserStatus.JOINED, None),
        (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.FORFEITED),
        (AsyncRaceRoomUserStatus.FORFEITED, AsyncRaceRoomUserStatus.STARTED),
        (AsyncRaceRoomUserStatus.FINISHED, None),
    ],
)
async def test_on_forfeit(skip_qtbot, default_blank_preset, before, after):
    window = create_window(skip_qtbot, create_room(default_blank_preset, self_status=before))
    await button_state_helper(window, after, window.ui.forfeit_button, window._on_forfeit)


@pytest.mark.parametrize("confirm_export", [False, True])
@pytest.mark.parametrize("prompt_join", ["refuse", "accept", "member"])
async def test_on_join_and_forfeit(
    skip_qtbot, default_blank_preset, mocker: pytest_mock.MockFixture, prompt_join, confirm_export
):
    mock_prompt = mocker.patch(
        "randovania.gui.lib.async_dialog.yes_no_prompt", autospec=True, return_value=prompt_join != "refuse"
    )
    mock_dialog = mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog",
        autospec=True,
        return_value=QtWidgets.QDialog.DialogCode.Accepted if confirm_export else QtWidgets.QDialog.DialogCode.Rejected,
    )
    mock_export = mocker.patch("randovania.gui.lib.game_exporter.export_game", autospec=True)

    window = create_window(
        skip_qtbot,
        create_room(
            default_blank_preset,
            self_status=AsyncRaceRoomUserStatus.JOINED
            if prompt_join == "member"
            else AsyncRaceRoomUserStatus.NOT_MEMBER,
        ),
    )
    network_client: AsyncMock = window._network_client
    window.refresh_data = AsyncMock()
    window.preset = preset = MagicMock(spec=VersionedPreset)
    export_dialog_class: MagicMock = preset.game.gui.export_dialog

    # Run
    await window._on_join_and_export()

    # Assert

    # Confirm joining
    if prompt_join == "member":
        mock_prompt.assert_not_called()
    else:
        mock_prompt.assert_awaited_once_with(window, ANY, ANY)

    if prompt_join == "refuse":
        export_dialog_class.assert_not_called()
        return

    # Game Export dialog
    export_dialog_class.assert_called_once_with(
        window._options,
        preset.get_preset.return_value.configuration,
        window.room.game_details.word_hash,
        False,
        [preset.game],
    )
    mock_dialog.assert_awaited_once_with(export_dialog_class.return_value)

    # Calling join and export
    if not confirm_export:
        network_client.async_race_join_and_export.assert_not_called()
        return

    network_client.async_race_join_and_export.assert_awaited_once_with(window.room, ANY)
    export_dialog_class.return_value.save_options.assert_called_once_with()

    # Exporter!
    mock_export.assert_awaited_once_with(
        exporter=preset.game.exporter,
        export_dialog=export_dialog_class.return_value,
        patch_data=network_client.async_race_join_and_export.return_value,
        layout_for_spoiler=None,
        background=window,
        progress_update_signal=window.progress_update_signal,
    )

    window.refresh_data.assert_awaited_once_with()
