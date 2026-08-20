from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from randovania.gui.async_race_room_window import AsyncRaceRoomWindow
from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.gui.widgets.audit_log_model import AuditEntryListDatabaseModel
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common.async_race_room import (
    AsyncRaceEntryData,
    AsyncRaceRoomAdminData,
    AsyncRaceRoomEntry,
    AsyncRaceRoomRaceStatus,
    AsyncRaceRoomUserStatus,
    AsyncRaceTeamEntry,
    AsyncRaceTeamMember,
    AsyncRaceWorldEntry,
)
from randovania.network_common.audit import AuditEntry
from randovania.network_common.game_details import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.network_common.user import RandovaniaUser

if TYPE_CHECKING:
    import pytest_mock
    from pytestqt.qtbot import QtBot

    from randovania.gui.dialog.async_race.async_race_admin_dialog import AsyncRaceAdminDialog
    from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog
    from randovania.interface_common.options import Options
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


def create_window(skip_qtbot: QtBot, room: AsyncRaceRoomEntry, options: Options) -> AsyncRaceRoomWindow:
    window = AsyncRaceRoomWindow(room, MagicMock(spec=QtNetworkClient), options, MagicMock())
    window._refresh_timer.stop()
    window._update_time_labels_timer.stop()
    window._refresh_timer = MagicMock()
    window._update_time_labels_timer = MagicMock()
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
async def test_on_start(skip_qtbot, options, default_blank_preset, before, after):
    window = create_window(skip_qtbot, create_room(default_blank_preset, self_status=before), options)
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
async def test_on_pause(skip_qtbot, options, default_blank_preset, before, after):
    window = create_window(skip_qtbot, create_room(default_blank_preset, self_status=before), options)
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
async def test_on_finish(skip_qtbot, options, default_blank_preset, before, after):
    window = create_window(skip_qtbot, create_room(default_blank_preset, self_status=before), options)
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
async def test_on_forfeit(skip_qtbot, options, default_blank_preset, before, after):
    window = create_window(skip_qtbot, create_room(default_blank_preset, self_status=before), options)
    await button_state_helper(window, after, window.ui.forfeit_button, window._on_forfeit)


@pytest.mark.parametrize("confirm_export", [False, True])
@pytest.mark.parametrize("prompt_join", ["refuse", "accept", "member"])
async def test_on_join_and_forfeit(
    skip_qtbot, options, default_blank_preset, mocker: pytest_mock.MockFixture, prompt_join, confirm_export
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
        options,
    )
    network_client: AsyncMock = window._network_client
    window.refresh_data = AsyncMock()
    preset = MagicMock(spec=VersionedPreset)
    window.presets = [preset]
    preset.game.value = default_blank_preset.game.value
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
        background=window.ui.background_task_widget,
    )

    window.refresh_data.assert_awaited_once_with()


async def test_on_view_user_entries(skip_qtbot, options, default_blank_preset, mocker: pytest_mock.MockFixture):
    def execute_dialog_effect(dialog: AsyncRaceAdminDialog):
        dialog.model.setData(dialog.model.index(1, 4), "true", Qt.ItemDataRole.EditRole)
        return QtWidgets.QDialog.DialogCode.Accepted

    mock_dialog = mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog",
        autospec=True,
        side_effect=execute_dialog_effect,
    )

    window = create_window(
        skip_qtbot, create_room(default_blank_preset, self_status=AsyncRaceRoomUserStatus.JOINED), options
    )
    window._network_client.async_race_admin_update_entries = AsyncMock(return_value=window.room)
    window._network_client.async_race_admin_get_admin_data.return_value = AsyncRaceRoomAdminData(
        users=[
            AsyncRaceEntryData(
                user=RandovaniaUser(id=1235, name="user"),
                join_date=datetime.datetime(2020, 5, 6, 0, 0, tzinfo=datetime.UTC),
                start_date=datetime.datetime(2020, 6, 6, 0, 0, tzinfo=datetime.UTC),
                finish_date=datetime.datetime(2020, 7, 7, 0, 0, tzinfo=datetime.UTC),
                forfeit=False,
                pauses=[],
                submission_notes="notes",
                proof_url="url",
            ),
            AsyncRaceEntryData(
                user=RandovaniaUser(id=2000, name="user2"),
                join_date=datetime.datetime(2020, 5, 6, 0, 0, tzinfo=datetime.UTC),
                start_date=datetime.datetime(2020, 6, 6, 0, 0, tzinfo=datetime.UTC),
                finish_date=datetime.datetime(2020, 7, 7, 0, 0, tzinfo=datetime.UTC),
                forfeit=False,
                pauses=[],
                submission_notes="",
                proof_url="",
            ),
        ]
    )

    # Run
    await window._on_view_user_entries()

    # Assert
    window._network_client.async_race_admin_get_admin_data.assert_awaited_once_with(window.room.id)
    mock_dialog.assert_awaited_once()
    window._network_client.async_race_admin_update_entries.assert_awaited_once_with(
        window.room.id,
        [
            AsyncRaceEntryData(
                user=RandovaniaUser(id=2000, name="user2"),
                join_date=datetime.datetime(2020, 5, 6, 0, 0, tzinfo=datetime.UTC),
                start_date=datetime.datetime(2020, 6, 6, 0, 0, tzinfo=datetime.UTC),
                finish_date=datetime.datetime(2020, 7, 7, 0, 0, tzinfo=datetime.UTC),
                forfeit=True,
                pauses=[],
                submission_notes="",
                proof_url="",
            ),
        ],
    )


@pytest.mark.parametrize("cancel", [False, True])
async def test_on_submit_proof(skip_qtbot, options, default_blank_preset, mocker: pytest_mock.MockFixture, cancel):
    mock_dialog = mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog",
        autospec=True,
        return_value=QtWidgets.QDialog.DialogCode.Rejected if cancel else QtWidgets.QDialog.DialogCode.Accepted,
    )

    window = create_window(
        skip_qtbot, create_room(default_blank_preset, self_status=AsyncRaceRoomUserStatus.FINISHED), options
    )
    window._network_client.async_race_get_own_proof.return_value = (
        "your extensive submission notes",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    )

    # Run
    await window._on_submit_proof()

    # Assert
    window._network_client.async_race_get_own_proof.assert_awaited_once_with(window.room.id)
    mock_dialog.assert_awaited_once()
    if cancel:
        window._network_client.async_race_submit_proof.assert_not_awaited()
    else:
        window._network_client.async_race_submit_proof.assert_awaited_once_with(
            window.room.id,
            "your extensive submission notes",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )


async def test_on_view_audit_log(skip_qtbot, options, default_blank_preset, mocker: pytest_mock.MockFixture):
    mock_dialog = mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog",
        autospec=True,
    )

    window = create_window(
        skip_qtbot, create_room(default_blank_preset, self_status=AsyncRaceRoomUserStatus.FINISHED), options
    )
    window._network_client.async_race_get_audit_log.return_value = [
        AuditEntry(
            user="The Name",
            message="Did something",
            time=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.UTC),
        ),
        AuditEntry(
            user="Other",
            message="Did something else",
            time=datetime.datetime(2020, 5, 3, 10, 20, tzinfo=datetime.UTC),
        ),
    ]

    # Run
    await window._on_view_audit_log()

    # Assert
    mock_dialog.assert_awaited_once()
    dialog: QtWidgets.QDialog = mock_dialog.call_args[0][0]
    table_view: QtWidgets.QTableView = dialog.findChild(QtWidgets.QTableView)
    model = table_view.model()
    assert isinstance(model, AuditEntryListDatabaseModel)
    assert len(model.db) == 2


async def test_get_livesplit_url(skip_qtbot, options, default_blank_preset, mocker: pytest_mock.MockFixture):
    mock_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog")
    mock_set_clipboard = mocker.patch("randovania.gui.lib.common_qt_lib.set_clipboard")

    window = create_window(
        skip_qtbot, create_room(default_blank_preset, self_status=AsyncRaceRoomUserStatus.JOINED), options
    )
    window._network_client.async_race_get_livesplit_url.return_value = "https://server/the-url"

    # Run
    await window._get_livesplit_url()

    # Assert
    mock_set_clipboard.assert_called_once_with("https://server/the-url")
    mock_dialog.assert_awaited_once()
    dialog: TextPromptDialog = mock_dialog.call_args[0][0]
    assert dialog.text_value == "https://server/the-url"


@pytest.mark.parametrize("same_id", [False, True])
async def test_on_data_from_server(skip_qtbot, options, default_blank_preset, same_id):
    window = create_window(
        skip_qtbot, create_room(default_blank_preset, self_status=AsyncRaceRoomUserStatus.JOINED), options
    )
    window.on_room_details = MagicMock()
    new_room = MagicMock()
    new_room.id = 1000 if same_id else 50

    # Run
    window.on_data_from_server(new_room)

    # Assert
    if same_id:
        window.on_room_details.assert_called_once_with(new_room)
    else:
        window.on_room_details.assert_not_called()


def create_team_room(
    preset: Preset,
    *,
    self_status: AsyncRaceRoomUserStatus = AsyncRaceRoomUserStatus.NOT_MEMBER,
    self_team_id: int | None = None,
    self_is_captain: bool = False,
    self_has_exported: bool = False,
    is_admin: bool = False,
    race_status: AsyncRaceRoomRaceStatus = AsyncRaceRoomRaceStatus.ACTIVE,
    own_team_session_id: int | None = 55,
    shared_team_timer: bool = True,
    member_statuses: dict[int, AsyncRaceRoomUserStatus] | None = None,
    member_times: dict[int, datetime.timedelta] | None = None,
    rival_status: AsyncRaceRoomUserStatus | None = AsyncRaceRoomUserStatus.STARTED,
) -> AsyncRaceRoomEntry:
    """A two world room raced by teams, with one team of two and one that's still looking."""
    raw_preset = VersionedPreset.with_preset(preset).as_bytes()
    statuses = member_statuses or {}
    times = member_times or {}

    def member(user: RandovaniaUser) -> AsyncRaceTeamMember:
        return AsyncRaceTeamMember(
            user=user,
            status=statuses.get(user.id, AsyncRaceRoomUserStatus.JOINED),
            time=times.get(user.id),
        )

    return create_room(preset, self_status=self_status, race_status=race_status, is_admin=is_admin).model_copy(
        update={
            "presets_raw": [raw_preset, raw_preset],
            "world_count": 2,
            "self_team_id": self_team_id,
            "self_is_captain": self_is_captain,
            "self_has_exported": self_has_exported,
            "shared_team_timer": shared_team_timer,
            "teams": [
                AsyncRaceTeamEntry(
                    id=1,
                    name="First Team",
                    status=AsyncRaceRoomUserStatus.JOINED,
                    members=[member(RandovaniaUser(10, "Alice")), member(RandovaniaUser(11, "Bob"))],
                    captain=RandovaniaUser(10, "Alice"),
                    session_id=own_team_session_id,
                    worlds=[
                        AsyncRaceWorldEntry(
                            world_uuid=uuid.UUID("1179c986-758a-4170-9b07-fe4541d78db0"),
                            order=0,
                            name="World 1",
                            claimed_by=[RandovaniaUser(10, "Alice")],
                        ),
                        AsyncRaceWorldEntry(
                            world_uuid=uuid.UUID("6b5ac1a1-d250-4f05-a5fb-ae37e8a92165"),
                            order=1,
                            name="World 2",
                            claimed_by=[],
                        ),
                    ],
                ),
                AsyncRaceTeamEntry(
                    id=2,
                    name="Second Team",
                    status=rival_status,
                    members=[member(RandovaniaUser(12, "Carol"))],
                    captain=RandovaniaUser(12, "Carol"),
                    session_id=None,
                    worlds=[],
                ),
            ],
        }
    )


def table_contents(table: QtWidgets.QTableWidget) -> list[list[str]]:
    return [
        [table.item(row, column).text() for column in range(table.columnCount())] for row in range(table.rowCount())
    ]


def test_teams_group_hidden_without_teams(skip_qtbot, options, default_blank_preset):
    window = create_window(skip_qtbot, create_room(default_blank_preset), options)

    assert not window.ui.teams_group.isVisibleTo(window)
    assert window.ui.join_and_export_button.isVisibleTo(window)
    assert window.ui.customize_cosmetic_button.isVisibleTo(window)


def test_teams_group_replaces_export_button(skip_qtbot, options, default_blank_preset):
    """A team exports from its own multiplayer session, so the room's export button is gone."""
    window = create_window(skip_qtbot, create_team_room(default_blank_preset), options)

    assert window.ui.teams_group.isVisibleTo(window)
    assert not window.ui.join_and_export_button.isVisibleTo(window)
    assert not window.ui.customize_cosmetic_button.isVisibleTo(window)


def test_teams_table_contents(skip_qtbot, options, default_blank_preset):
    window = create_window(skip_qtbot, create_team_room(default_blank_preset), options)

    assert table_contents(window.ui.teams_table) == [
        ["First Team", "Alice (captain), Bob (2)", "joined"],
        ["Second Team", "Carol (captain) (1)", "started"],
    ]


def test_teams_table_shows_member_status_when_accumulating(skip_qtbot, options, default_blank_preset):
    """A team on separate timers shows each member's own state, since they all move apart."""
    window = create_window(
        skip_qtbot,
        create_team_room(
            default_blank_preset,
            shared_team_timer=False,
            member_statuses={
                10: AsyncRaceRoomUserStatus.STARTED,
                11: AsyncRaceRoomUserStatus.FINISHED,
            },
        ),
        options,
    )

    assert table_contents(window.ui.teams_table)[0] == [
        "First Team",
        "Alice (captain) - started, Bob - finished (2)",
        "joined",
    ]


def test_worlds_table_shows_own_team_claims(skip_qtbot, options, default_blank_preset):
    window = create_window(
        skip_qtbot,
        create_team_room(default_blank_preset, self_team_id=1, self_status=AsyncRaceRoomUserStatus.JOINED),
        options,
    )

    assert table_contents(window.ui.worlds_table) == [
        ["World 1", default_blank_preset.game.long_name, "Alice"],
        ["World 2", default_blank_preset.game.long_name, "(unclaimed)"],
    ]


def test_worlds_table_without_a_team(skip_qtbot, options, default_blank_preset):
    """Someone with no team isn't told who's playing what, since they see no team's session."""
    window = create_window(skip_qtbot, create_team_room(default_blank_preset), options)

    table = window.ui.worlds_table
    assert [table.item(row, 2).text() for row in range(table.rowCount())] == ["", ""]
    assert [table.item(row, 0).text() for row in range(table.rowCount())] == ["World 1", "World 2"]


def test_team_buttons_without_a_team(skip_qtbot, options, default_blank_preset):
    window = create_window(skip_qtbot, create_team_room(default_blank_preset), options)

    assert window.ui.create_team_button.isEnabled()
    assert window.ui.join_team_button.isEnabled()
    assert not window.ui.leave_team_button.isEnabled()
    assert not window.ui.team_join_code_button.isEnabled()


def test_team_buttons_with_a_team(skip_qtbot, options, default_blank_preset):
    window = create_window(
        skip_qtbot,
        create_team_room(default_blank_preset, self_team_id=1, self_status=AsyncRaceRoomUserStatus.JOINED),
        options,
    )

    assert not window.ui.create_team_button.isEnabled()
    assert not window.ui.join_team_button.isEnabled()
    assert window.ui.leave_team_button.isEnabled()
    assert window.ui.team_join_code_button.isEnabled()


def test_leave_team_blocked_after_exporting(skip_qtbot, options, default_blank_preset):
    window = create_window(
        skip_qtbot,
        create_team_room(
            default_blank_preset,
            self_team_id=1,
            self_status=AsyncRaceRoomUserStatus.JOINED,
            self_has_exported=True,
        ),
        options,
    )

    assert not window.ui.leave_team_button.isEnabled()
    assert window.ui.leave_team_button.toolTip() == "Can't leave a team after exporting a game"


@pytest.mark.parametrize("is_captain", [False, True])
def test_timer_buttons_only_for_captain(skip_qtbot, options, default_blank_preset, is_captain):
    """A team shares one timer, so only its captain moves it."""
    window = create_window(
        skip_qtbot,
        create_team_room(
            default_blank_preset,
            self_team_id=1,
            self_is_captain=is_captain,
            self_status=AsyncRaceRoomUserStatus.JOINED,
        ),
        options,
    )

    assert window.ui.start_button.isEnabled() == is_captain
    assert window.ui.livesplit_button.isEnabled() == is_captain
    if not is_captain:
        assert window.ui.start_button.toolTip() == "Only the team's captain can start or forfeit the race"
        assert window.ui.pause_button.toolTip() == "Only the team's captain can control the timer"


async def test_on_create_team(skip_qtbot, options, default_blank_preset, mocker: pytest_mock.MockFixture):
    mock_prompt = mocker.patch(
        "randovania.gui.dialog.text_prompt_dialog.TextPromptDialog.prompt",
        autospec=True,
        side_effect=["My Team", None],
    )
    mocker.patch("randovania.gui.lib.common_qt_lib.set_clipboard")

    window = create_window(skip_qtbot, create_team_room(default_blank_preset), options)
    network_client: AsyncMock = window._network_client
    network_client.async_race_create_team.return_value = create_team_room(
        default_blank_preset, self_team_id=1, self_is_captain=True, self_status=AsyncRaceRoomUserStatus.JOINED
    )
    network_client.async_race_get_team_join_code.return_value = "TheCode"

    # Run
    await window._on_create_team()

    # Assert
    network_client.async_race_create_team.assert_awaited_once_with(ANY, "My Team")
    network_client.async_race_get_team_join_code.assert_awaited_once_with(window.room.id)
    assert mock_prompt.await_count == 2
    assert window.room.self_team_id == 1


async def test_on_create_team_cancelled(skip_qtbot, options, default_blank_preset, mocker: pytest_mock.MockFixture):
    mocker.patch("randovania.gui.dialog.text_prompt_dialog.TextPromptDialog.prompt", autospec=True, return_value=None)

    window = create_window(skip_qtbot, create_team_room(default_blank_preset), options)

    # Run
    await window._on_create_team()

    # Assert
    window._network_client.async_race_create_team.assert_not_called()


async def test_on_join_team(skip_qtbot, options, default_blank_preset, mocker: pytest_mock.MockFixture):
    mocker.patch(
        "randovania.gui.dialog.text_prompt_dialog.TextPromptDialog.prompt", autospec=True, return_value="  TheCode  "
    )

    window = create_window(skip_qtbot, create_team_room(default_blank_preset), options)
    network_client: AsyncMock = window._network_client
    network_client.async_race_join_team.return_value = create_team_room(
        default_blank_preset, self_team_id=1, self_status=AsyncRaceRoomUserStatus.JOINED
    )

    # Run
    await window._on_join_team()

    # Assert
    network_client.async_race_join_team.assert_awaited_once_with(window.room.id, "TheCode")
    assert window.room.self_team_id == 1


@pytest.mark.parametrize("confirm", [False, True])
async def test_on_leave_team(skip_qtbot, options, default_blank_preset, mocker: pytest_mock.MockFixture, confirm):
    mocker.patch("randovania.gui.lib.async_dialog.yes_no_prompt", autospec=True, return_value=confirm)

    window = create_window(
        skip_qtbot,
        create_team_room(default_blank_preset, self_team_id=1, self_status=AsyncRaceRoomUserStatus.JOINED),
        options,
    )
    network_client: AsyncMock = window._network_client
    network_client.async_race_leave_team.return_value = create_team_room(default_blank_preset)

    # Run
    await window._on_leave_team()

    # Assert
    if confirm:
        network_client.async_race_leave_team.assert_awaited_once_with(1000)
        assert window.room.self_team_id is None
    else:
        network_client.async_race_leave_team.assert_not_called()


async def test_on_copy_join_code(skip_qtbot, options, default_blank_preset, mocker: pytest_mock.MockFixture):
    mock_clipboard = mocker.patch("randovania.gui.lib.common_qt_lib.set_clipboard")
    mock_prompt = mocker.patch(
        "randovania.gui.dialog.text_prompt_dialog.TextPromptDialog.prompt", autospec=True, return_value=None
    )

    window = create_window(
        skip_qtbot,
        create_team_room(default_blank_preset, self_team_id=1, self_status=AsyncRaceRoomUserStatus.JOINED),
        options,
    )
    window._network_client.async_race_get_team_join_code.return_value = "TheCode"

    # Run
    await window._on_copy_join_code()

    # Assert
    mock_clipboard.assert_called_once_with("TheCode")
    assert mock_prompt.call_args.kwargs["initial_value"] == "TheCode"
    assert mock_prompt.call_args.kwargs["read_only"]
    assert window.isEnabled()


async def test_on_open_own_session(skip_qtbot, options, default_blank_preset):
    """Your own team's session is already yours, so there's nothing to join first."""
    window = create_window(
        skip_qtbot,
        create_team_room(default_blank_preset, self_team_id=1, self_status=AsyncRaceRoomUserStatus.JOINED),
        options,
    )
    window._window_manager.ensure_multiplayer_session_window = AsyncMock()
    window._context_menu_team = window.room.teams[0]

    # Run
    await window._on_open_session()

    # Assert
    network_client: AsyncMock = window._network_client
    network_client.join_multiplayer_session.assert_not_called()
    network_client.listen_to_session.assert_awaited_once_with(55, True)
    window._window_manager.ensure_multiplayer_session_window.assert_awaited_once_with(network_client, 55, options)


async def test_on_open_another_teams_session(skip_qtbot, options, default_blank_preset):
    """The room's creator gets a session id for every team, but has to join before listening."""
    room = create_team_room(default_blank_preset, is_admin=True)
    room.teams[1].session_id = 66
    window = create_window(skip_qtbot, room, options)
    window._window_manager.ensure_multiplayer_session_window = AsyncMock()
    window._context_menu_team = room.teams[1]

    # Run
    await window._on_open_session()

    # Assert
    network_client: AsyncMock = window._network_client
    network_client.join_multiplayer_session.assert_awaited_once_with(66, None)
    network_client.listen_to_session.assert_awaited_once_with(66, True)


async def test_on_open_session_without_one(skip_qtbot, options, default_blank_preset):
    window = create_window(skip_qtbot, create_team_room(default_blank_preset), options)
    window._context_menu_team = window.room.teams[1]

    # Run
    await window._on_open_session()

    # Assert
    window._network_client.listen_to_session.assert_not_called()


@pytest.mark.parametrize("is_admin", [False, True])
def test_administration_menu_is_admin_only(skip_qtbot, options, default_blank_preset, is_admin):
    """
    Every administration action, the audit log included: the log timestamps each participant's
    state changes, which is what the leaderboard withholds until the race is over.
    """
    window = create_window(skip_qtbot, create_room(default_blank_preset, is_admin=is_admin), options)

    assert window._view_audit_log_action.isEnabled() == is_admin
    assert window._change_options_action.isEnabled() == is_admin
    assert window._view_user_entries_action.isEnabled() == is_admin


def test_participation_label_reports_own_time(skip_qtbot, options, default_blank_preset):
    """A finished run is told its time right away, well before the leaderboard opens."""
    room = create_room(default_blank_preset, self_status=AsyncRaceRoomUserStatus.FINISHED).model_copy(
        update={"self_time": datetime.timedelta(hours=1, minutes=2, seconds=3)}
    )
    window = create_window(skip_qtbot, room, options)

    assert window.ui.participation_label.isVisibleTo(window)
    assert window.ui.participation_label.text() == "Your time: 1h 2min 3s"


def test_participation_label_reports_the_teams_time(skip_qtbot, options, default_blank_preset):
    """In a race played in teams the time is the team's, however that team is timed."""
    room = create_team_room(
        default_blank_preset,
        self_status=AsyncRaceRoomUserStatus.FINISHED,
        self_team_id=1,
    ).model_copy(update={"self_time": datetime.timedelta(minutes=90)})
    window = create_window(skip_qtbot, room, options)

    assert window.ui.participation_label.text() == "Your team's time: 1h 30min 0s"


def test_participation_label_hidden_while_racing(skip_qtbot, options, default_blank_preset):
    """Nothing to say about a run that is neither over nor complete."""
    window = create_window(
        skip_qtbot, create_room(default_blank_preset, self_status=AsyncRaceRoomUserStatus.STARTED), options
    )

    assert not window.ui.participation_label.isVisibleTo(window)
    assert window.ui.participation_label.text() == ""


def test_participation_label_after_the_race_ends(skip_qtbot, options, default_blank_preset):
    """Once the race is over, how it ended and the time are shown together."""
    room = create_room(
        default_blank_preset,
        self_status=AsyncRaceRoomUserStatus.FINISHED,
        race_status=AsyncRaceRoomRaceStatus.FINISHED,
    ).model_copy(update={"self_time": datetime.timedelta(hours=2)})
    window = create_window(skip_qtbot, room, options)

    assert window.ui.participation_label.text() == "Race has finished. You finished. Your time: 2h 0min 0s"


def test_participation_label_forfeit_has_no_time(skip_qtbot, options, default_blank_preset):
    """Giving up leaves no time, so only the outcome is reported."""
    window = create_window(
        skip_qtbot,
        create_room(
            default_blank_preset,
            self_status=AsyncRaceRoomUserStatus.FORFEITED,
            race_status=AsyncRaceRoomRaceStatus.FINISHED,
        ),
        options,
    )

    assert window.ui.participation_label.text() == "Race has finished. You forfeited."


def test_teams_table_shows_member_times_when_accumulating(skip_qtbot, options, default_blank_preset):
    """A member who is done shows the time they contributed to the team's total."""
    window = create_window(
        skip_qtbot,
        create_team_room(
            default_blank_preset,
            shared_team_timer=False,
            member_statuses={
                10: AsyncRaceRoomUserStatus.STARTED,
                11: AsyncRaceRoomUserStatus.FINISHED,
            },
            member_times={11: datetime.timedelta(hours=1, minutes=15)},
        ),
        options,
    )

    assert table_contents(window.ui.teams_table)[0][1] == "Alice (captain) - started, Bob - finished (1h 15min 0s) (2)"


def test_teams_table_hides_withheld_status(skip_qtbot, options, default_blank_preset):
    """A team whose progress the server withholds is listed without a status."""
    window = create_window(
        skip_qtbot,
        create_team_room(default_blank_preset, self_team_id=1, rival_status=None),
        options,
    )

    assert table_contents(window.ui.teams_table) == [
        ["First Team", "Alice (captain), Bob (2)", "joined"],
        ["Second Team", "Carol (captain) (1)", "-"],
    ]


def test_teams_table_hides_withheld_member_status(skip_qtbot, options, default_blank_preset):
    """Members of a withheld team carry no status either, so none is rendered next to them."""
    room = create_team_room(
        default_blank_preset,
        self_team_id=1,
        shared_team_timer=False,
        rival_status=None,
        member_statuses={10: AsyncRaceRoomUserStatus.FINISHED},
        member_times={10: datetime.timedelta(hours=1)},
    )
    rival = room.teams[1].model_copy(
        update={"members": [AsyncRaceTeamMember(user=RandovaniaUser(12, "Carol"))]},
    )
    window = create_window(skip_qtbot, room.model_copy(update={"teams": [room.teams[0], rival]}), options)

    assert table_contents(window.ui.teams_table) == [
        ["First Team", "Alice (captain) - finished (1h 0min 0s), Bob (2)", "joined"],
        ["Second Team", "Carol (captain) (1)", "-"],
    ]
