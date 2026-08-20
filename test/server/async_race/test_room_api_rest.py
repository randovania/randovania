"""
End-to-end tests for the async race room REST API: a real `NetworkClient` talking to a real server.

The tests in `test_room_api.py` call the endpoint functions directly, which skips everything FastAPI
does around them. These tests exist to cover exactly that gap: request/response serialization,
query parameters, status codes and error decoding.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import pytest

from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.layout.layout_description import LayoutDescription
from randovania.network_common import error
from randovania.network_common.async_race_room import (
    AsyncRaceRoomRaceStatus,
    AsyncRaceRoomUserStatus,
    AsyncRaceSettings,
)
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server.database import AsyncRaceEntry, AsyncRaceEntryPause, AsyncRaceRoom, User

if TYPE_CHECKING:
    import pytest_mock

    from randovania.network_client.network_client import NetworkClient

# The room in `simple_room` runs from 2020-05-10 to 2020-06-10
DURING_RACE = datetime.datetime(2020, 5, 12, tzinfo=datetime.UTC)
BEFORE_RACE = datetime.datetime(2019, 5, 12, tzinfo=datetime.UTC)
AFTER_RACE = datetime.datetime(2021, 5, 12, tzinfo=datetime.UTC)

CREATOR_ID = 1234
PLAYER_ID = 1235


@pytest.fixture
def now(mocker: pytest_mock.MockerFixture):
    """Controls what the server considers to be the current time."""

    def set_now(value: datetime.datetime) -> datetime.datetime:
        mocker.patch("randovania.server.lib.datetime_now", return_value=value)
        return value

    set_now(DURING_RACE)
    return set_now


@pytest.fixture
def creator(make_live_client, simple_room) -> NetworkClient:
    return make_live_client(CREATOR_ID)


@pytest.fixture
def player(make_live_client, simple_room) -> NetworkClient:
    return make_live_client(PLAYER_ID)


async def test_get_async_race_room_list(creator: NetworkClient, simple_room, now):
    # Run
    result = await creator.get_async_race_room_list(ignore_limit=True)

    # Assert
    assert len(result) == 1
    assert result[0].id == simple_room.id
    assert result[0].name == "Debug"
    assert result[0].game_summary() == "Metroid Prime 2: Echoes"
    assert result[0].race_status == AsyncRaceRoomRaceStatus.ACTIVE
    assert result[0].creation_date == datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.UTC)


async def test_get_async_race_room_list_with_limit(creator: NetworkClient, simple_room, now):
    # Run
    result = await creator.get_async_race_room_list(ignore_limit=False)

    # Assert
    assert [it.id for it in result] == [simple_room.id]


async def test_create_async_race_room(creator: NetworkClient, simple_room, test_files_dir, now):
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "prime2_seed_b.rdvgame"))
    settings = AsyncRaceSettings(
        name="A New Room",
        password=None,
        start_date=datetime.datetime(2020, 6, 1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2020, 7, 1, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        allow_pause=True,
    )

    # Run
    result = await creator.create_async_race_room(description, settings)

    # Assert
    assert result.name == "A New Room"
    assert result.is_admin
    assert result.race_status == AsyncRaceRoomRaceStatus.SCHEDULED
    assert result.start_date == settings.start_date
    assert result.end_date == settings.end_date
    # The layout survived the base64 round trip
    assert AsyncRaceRoom.get_by_id(result.id).layout_description == description
    # And so did the presets
    assert [preset.get_preset() for preset in result.presets] == list(description.all_presets)


async def test_create_async_race_room_invalid_name(creator: NetworkClient, simple_room, test_files_dir, now):
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "prime2_seed_b.rdvgame"))
    settings = AsyncRaceSettings(
        name="",
        password=None,
        start_date=datetime.datetime(2020, 6, 1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2020, 7, 1, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        allow_pause=True,
    )

    # Run
    with pytest.raises(error.InvalidActionError, match="Invalid session name length"):
        await creator.create_async_race_room(description, settings)


async def test_get_async_race_room_no_password(player: NetworkClient, simple_room, now):
    # Run
    result = await player.get_async_race_room(simple_room.id, None)

    # Assert
    assert result.name == "Debug"
    assert not result.is_admin
    assert result.self_status == AsyncRaceRoomUserStatus.STARTED


async def test_get_async_race_room_with_password(player: NetworkClient, simple_room, now):
    simple_room.password = "TheSecret"
    simple_room.save()

    # Run
    result = await player.get_async_race_room(simple_room.id, "TheSecret")

    # Assert
    assert result.name == "Debug"


async def test_get_async_race_room_wrong_password(player: NetworkClient, simple_room, now):
    simple_room.password = "TheSecret"
    simple_room.save()

    # Run
    with pytest.raises(error.WrongPasswordError):
        await player.get_async_race_room(simple_room.id, "NotTheSecret")


async def test_async_race_refresh_room(player: NetworkClient, simple_room, now):
    room = await player.get_async_race_room(simple_room.id, None)

    # Run
    result = await player.async_race_refresh_room(room)

    # Assert
    assert result.id == room.id
    assert result.self_status == AsyncRaceRoomUserStatus.STARTED


async def test_async_race_change_room_settings(creator: NetworkClient, simple_room, now):
    settings = AsyncRaceSettings(
        name="Renamed Room",
        password=None,
        start_date=datetime.datetime(2020, 5, 11, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2020, 8, 10, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.HIDDEN,
        allow_pause=False,
    )

    # Run
    result = await creator.async_race_change_room_settings(simple_room.id, settings)

    # Assert
    assert result.name == "Renamed Room"
    assert result.visibility == MultiplayerSessionVisibility.HIDDEN
    assert not result.allow_pause
    assert result.end_date == settings.end_date


async def test_async_race_change_room_settings_not_admin(player: NetworkClient, simple_room, now):
    settings = AsyncRaceSettings(
        name="Renamed Room",
        password=None,
        start_date=datetime.datetime(2020, 5, 11, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2020, 8, 10, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        allow_pause=False,
    )

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        await player.async_race_change_room_settings(simple_room.id, settings)


async def test_async_race_join_and_export(creator: NetworkClient, simple_room, now, mocker: pytest_mock.MockFixture):
    """
    `BaseCosmeticPatches` is abstract and the client always sends a concrete subclass,
    so the server can only decode it after it knows the room's game.
    """
    mock_create_data = mocker.patch(
        "randovania.games.prime2.exporter.patch_data_factory.EchoesPatchDataFactory.create_data",
        return_value={"the": "patcher data"},
    )
    room = await creator.get_async_race_room(simple_room.id, None)
    cosmetic = EchoesCosmeticPatches(open_map=False, unvisited_room_names=False)

    # Run
    result = await creator.async_race_join_and_export(room, cosmetic)

    # Assert
    assert result == {"the": "patcher data"}
    mock_create_data.assert_called_once()

    # The concrete subclass reached the patch data factory, not a bare BaseCosmeticPatches
    data_factory = mock_create_data.call_args_list[0].args[0]
    assert data_factory is not None
    assert AsyncRaceEntry.entry_for(simple_room, User.get_by_id(CREATOR_ID)) is not None


async def test_async_race_join_and_export_wrong_game_cosmetics(creator: NetworkClient, simple_room, now):
    """Cosmetic patches for a different game must be rejected, not silently ignored."""
    from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches

    room = await creator.get_async_race_room(simple_room.id, None)

    # Run
    with pytest.raises(error.InvalidActionError, match="Invalid cosmetic patches"):
        await creator.async_race_join_and_export(room, PrimeCosmeticPatches())

    # Assert
    assert AsyncRaceEntry.entry_for(simple_room, User.get_by_id(CREATOR_ID)) is None


async def test_async_race_join_and_export_not_active(creator: NetworkClient, simple_room, now):
    now(BEFORE_RACE)
    room = await creator.get_async_race_room(simple_room.id, None)

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        await creator.async_race_join_and_export(room, EchoesCosmeticPatches())


@pytest.mark.parametrize(
    "new_state",
    [AsyncRaceRoomUserStatus.PAUSED, AsyncRaceRoomUserStatus.FINISHED, AsyncRaceRoomUserStatus.FORFEITED],
)
async def test_async_race_change_state(player: NetworkClient, simple_room, now, new_state):
    # Run
    result = await player.async_race_change_state(simple_room.id, new_state)

    # Assert
    assert result.self_status == new_state
    entry = AsyncRaceEntry.entry_for(simple_room, User.get_by_id(PLAYER_ID))
    assert entry is not None
    assert entry.timer_status() == new_state


async def test_async_race_change_state_invalid_transition(player: NetworkClient, simple_room, now):
    # Run
    with pytest.raises(error.InvalidActionError, match="Unsupported state transition"):
        await player.async_race_change_state(simple_room.id, AsyncRaceRoomUserStatus.NOT_MEMBER)


async def test_async_race_change_state_not_a_member(creator: NetworkClient, simple_room, now):
    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        await creator.async_race_change_state(simple_room.id, AsyncRaceRoomUserStatus.STARTED)


async def test_async_race_submit_and_get_own_proof(player: NetworkClient, simple_room, now):
    await player.async_race_change_state(simple_room.id, AsyncRaceRoomUserStatus.FINISHED)

    # Run
    await player.async_race_submit_proof(simple_room.id, "Ran it clean", "https://example.com/vod")
    result = await player.async_race_get_own_proof(simple_room.id)

    # Assert
    assert result == ("Ran it clean", "https://example.com/vod")


async def test_async_race_submit_proof_before_finishing(player: NetworkClient, simple_room, now):
    # Run
    with pytest.raises(error.InvalidActionError, match="Only possible to submit proof after finishing"):
        await player.async_race_submit_proof(simple_room.id, "Notes", "https://example.com/vod")


async def test_async_race_get_audit_log(creator: NetworkClient, player: NetworkClient, simple_room, now):
    room = await creator.get_async_race_room(simple_room.id, None)
    await player.async_race_change_state(simple_room.id, AsyncRaceRoomUserStatus.FINISHED)

    # Run
    result = await creator.async_race_get_audit_log(room)

    # Assert
    assert [it.message for it in result] == ["Changed state from started to finished"]
    assert [it.user for it in result] == ["The Player"]
    # The time is set by a peewee field default, which isn't affected by the `now` fixture
    assert result[0].time.tzinfo is not None


async def test_async_race_get_audit_log_not_admin(player: NetworkClient, simple_room, now):
    """A racer can't read the log, even though they're in the room."""
    room = await player.get_async_race_room(simple_room.id, None)

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        await player.async_race_get_audit_log(room)


async def test_async_race_admin_get_admin_data(creator: NetworkClient, simple_room, now):
    # Run
    result = await creator.async_race_admin_get_admin_data(simple_room.id)

    # Assert
    assert len(result.users) == 1
    entry = result.users[0]
    assert entry.user.id == PLAYER_ID
    assert entry.join_date == datetime.datetime(2020, 5, 6, tzinfo=datetime.UTC)
    assert entry.start_date == datetime.datetime(2020, 5, 11, tzinfo=datetime.UTC)
    assert entry.finish_date is None
    assert entry.pauses == []


async def test_async_race_admin_get_admin_data_not_admin(player: NetworkClient, simple_room, now):
    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        await player.async_race_admin_get_admin_data(simple_room.id)


async def test_async_race_admin_get_admin_data_with_pauses(creator: NetworkClient, simple_room, now):
    entry = AsyncRaceEntry.entry_for(simple_room, User.get_by_id(PLAYER_ID))
    assert entry is not None
    AsyncRaceEntryPause.create(
        entry=entry,
        start=datetime.datetime(2020, 5, 11, 1, tzinfo=datetime.UTC),
        end=datetime.datetime(2020, 5, 11, 2, tzinfo=datetime.UTC),
    )

    # Run
    result = await creator.async_race_admin_get_admin_data(simple_room.id)

    # Assert
    assert [(it.start, it.end) for it in result.users[0].pauses] == [
        (
            datetime.datetime(2020, 5, 11, 1, tzinfo=datetime.UTC),
            datetime.datetime(2020, 5, 11, 2, tzinfo=datetime.UTC),
        )
    ]


async def test_async_race_admin_update_entries(creator: NetworkClient, simple_room, now):
    admin_data = await creator.async_race_admin_get_admin_data(simple_room.id)
    modified = admin_data.users[0].model_copy(
        update={"finish_date": datetime.datetime(2020, 5, 12, 5, tzinfo=datetime.UTC)}
    )

    # Run
    result = await creator.async_race_admin_update_entries(simple_room.id, [modified])

    # Assert
    assert result.id == simple_room.id
    updated = await creator.async_race_admin_get_admin_data(simple_room.id)
    assert updated.users[0].finish_date == datetime.datetime(2020, 5, 12, 5, tzinfo=datetime.UTC)


async def test_async_race_admin_update_entries_invalid_dates(creator: NetworkClient, simple_room, now):
    admin_data = await creator.async_race_admin_get_admin_data(simple_room.id)
    modified = admin_data.users[0].model_copy(
        update={"finish_date": datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC)}
    )

    # Run
    with pytest.raises(error.InvalidActionError, match="Invalid dates"):
        await creator.async_race_admin_update_entries(simple_room.id, [modified])


async def test_async_race_get_leaderboard(creator: NetworkClient, simple_room, now):
    entry = AsyncRaceEntry.entry_for(simple_room, User.get_by_id(PLAYER_ID))
    assert entry is not None
    entry.finish_datetime = datetime.datetime(2020, 5, 11, 2, 30, tzinfo=datetime.UTC)
    entry.save()
    room = await creator.get_async_race_room(simple_room.id, None)
    now(AFTER_RACE)

    # Run
    result = await creator.async_race_get_leaderboard(room)

    # Assert
    assert [it.display_name for it in result.entries] == ["The Player"]
    # timedelta has to survive being json encoded
    assert result.entries[0].time == datetime.timedelta(hours=2, minutes=30)


async def test_async_race_get_leaderboard_too_early(creator: NetworkClient, simple_room, now):
    room = await creator.get_async_race_room(simple_room.id, None)

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        await creator.async_race_get_leaderboard(room)


async def test_async_race_get_layout(creator: NetworkClient, simple_room, now):
    room = await creator.get_async_race_room(simple_room.id, None)
    now(AFTER_RACE)

    # Run
    result = await creator.async_race_get_layout(room)

    # Assert
    # The layout is binary, so it can't go through json at all
    assert result == simple_room.layout_description


async def test_async_race_get_layout_too_early(creator: NetworkClient, simple_room, now):
    room = await creator.get_async_race_room(simple_room.id, None)

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        await creator.async_race_get_layout(room)


async def test_async_race_get_livesplit_url(player: NetworkClient, simple_room, now):
    room = await player.get_async_race_room(simple_room.id, None)

    # Run
    result = await player.async_race_get_livesplit_url(room)

    # Assert
    assert result.startswith(f"ws://127.0.0.1:5000/async-race-room/{simple_room.id}/livesplit/")


async def test_async_race_get_livesplit_url_not_a_member(creator: NetworkClient, simple_room, now):
    room = await creator.get_async_race_room(simple_room.id, None)

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        await creator.async_race_get_livesplit_url(room)
