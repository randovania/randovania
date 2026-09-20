from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

from randovania.network_common import error
from randovania.network_common.async_race_room import (
    AsyncRaceEntryData,
    AsyncRaceRoomEntry,
    AsyncRaceRoomRaceStatus,
    AsyncRaceRoomUserStatus,
    AsyncRaceSettings,
    RaceRoomLeaderboard,
    RaceRoomLeaderboardEntry,
)
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.network_common.user import RandovaniaUser
from randovania.server import database
from randovania.server.async_race import room_api
from randovania.server.database import (
    AsyncRaceEntry,
    AsyncRaceRoom,
    AsyncRaceTeam,
    AsyncRaceTimerHolder,
    MultiplayerSession,
    User,
    World,
    WorldUserAssociation,
)

if TYPE_CHECKING:
    import pytest_mock


@pytest.fixture
def sa() -> MagicMock:
    """
    A ServerApp whose join code encryption is a plain round-trip, so a code created by one call
    can be read back by another.
    """
    sa = MagicMock()
    sa.get_current_user = AsyncMock()

    codes: dict[str, dict] = {}

    def encrypt(data: dict) -> str:
        code = f"code-{len(codes)}"
        codes[code] = data
        return code

    def decrypt(code: str) -> dict:
        return codes[code]

    sa.encrypt_and_b85_dict.side_effect = encrypt
    sa.decrypt_and_b85_dict.side_effect = decrypt
    return sa


@pytest.fixture
def _during_race(mocker: pytest_mock.MockFixture) -> None:
    """Places `now` between the room's start and end dates."""
    mocker.patch(
        "randovania.server.lib.datetime_now",
        return_value=datetime.datetime(2020, 5, 12, tzinfo=datetime.UTC),
    )


async def create_team(sa: MagicMock, room: AsyncRaceRoom, user_id: int, name: str) -> AsyncRaceRoomEntry:
    return await room_api.create_team(sa, User.get_by_id(user_id), room.id, "", name)


async def join_team(sa: MagicMock, room: AsyncRaceRoom, user_id: int, team: AsyncRaceTeam) -> AsyncRaceRoomEntry:
    assert team.captain_id is not None
    code = await room_api.get_team_join_code(User.get_by_id(team.captain_id), room.id)
    return await room_api.join_team(sa, User.get_by_id(user_id), room.id, code)


async def change_state(
    sa: MagicMock, room: AsyncRaceRoom, user_id: int, new_state: AsyncRaceRoomUserStatus
) -> AsyncRaceRoomEntry:
    return await room_api.change_state(sa, User.get_by_id(user_id), room.id, new_state)


def finish_run(holder: AsyncRaceTimerHolder, **delta: float) -> None:
    """Ends a run the given time after it started, without going through the API."""
    assert holder.start_datetime is not None
    holder.finish_datetime = holder.start_datetime + datetime.timedelta(**delta)
    holder.save()


def claim_world(team: AsyncRaceTeam, order: int, user_id: int) -> World:
    """Has a member of the team claim one of their session's worlds."""
    session = team.session
    assert session is not None
    world = session.get_ordered_worlds()[order]
    WorldUserAssociation.create(world=world, user=User.get_by_id(user_id))
    return world


@pytest.mark.usefixtures("_during_race")
async def test_create_team(sa, team_room):
    # Run
    result = await create_team(sa, team_room, 1235, "The Team")

    # Assert
    team = AsyncRaceTeam.get_by_id(1)
    assert team.name == "The Team"
    assert team.captain_id == 1235
    assert [member.user_id for member in team.all_members()] == [1235]

    # The team's multiworld gets a hidden session, with one world per preset of the layout
    session = team.session
    assert session is not None
    assert session.visibility == MultiplayerSessionVisibility.HIDDEN
    assert session.is_race_session
    assert [world.name for world in session.get_ordered_worlds()] == ["World 1", "World 2"]
    assert [membership.user_id for membership in session.members] == [1235]

    assert result.self_team_id == team.id
    assert result.self_is_captain
    assert result.uses_teams
    assert [(t.id, t.name, t.session_id) for t in result.teams] == [(1, "The Team", session.id)]

    assert [entry.as_entry().message for entry in team_room.audit_log] == ["Created team The Team."]


@pytest.mark.usefixtures("_during_race")
async def test_create_team_invalid_name(sa, team_room):
    with pytest.raises(error.InvalidActionError, match="Invalid team name length"):
        await create_team(sa, team_room, 1235, "")

    with pytest.raises(error.InvalidActionError, match="Invalid team name length"):
        await create_team(sa, team_room, 1235, "x" * (room_api.MAX_TEAM_NAME_LENGTH + 1))


@pytest.mark.usefixtures("_during_race")
async def test_create_team_twice(sa, team_room):
    await create_team(sa, team_room, 1235, "The Team")

    with pytest.raises(error.InvalidActionError, match="You are already part of a team in this room"):
        await create_team(sa, team_room, 1235, "Another Team")


@pytest.mark.usefixtures("_during_race")
async def test_create_team_not_a_team_room(sa, simple_room):
    with pytest.raises(error.InvalidActionError, match="This room is not played in teams"):
        await create_team(sa, simple_room, 1235, "The Team")


async def test_create_team_after_the_end(sa, team_room, mocker: pytest_mock.MockFixture):
    mocker.patch(
        "randovania.server.lib.datetime_now",
        return_value=datetime.datetime(2021, 5, 12, tzinfo=datetime.UTC),
    )

    with pytest.raises(error.NotAuthorizedForActionError):
        await create_team(sa, team_room, 1235, "The Team")


@pytest.mark.usefixtures("_during_race")
async def test_join_team(sa, team_room):
    await create_team(sa, team_room, 1235, "The Team")
    team = AsyncRaceTeam.get_by_id(1)

    # Run
    result = await join_team(sa, team_room, 1236, team)

    # Assert
    assert [member.user_id for member in team.all_members()] == [1235, 1236]
    assert result.self_team_id == team.id
    assert not result.self_is_captain

    session = team.session
    assert session is not None
    assert sorted(membership.user_id for membership in session.members) == [1235, 1236]

    assert [entry.as_entry().message for entry in team_room.audit_log] == [
        "Created team The Team.",
        "Joined team The Team.",
    ]


@pytest.mark.usefixtures("_during_race")
async def test_join_team_has_no_size_limit(sa, team_room):
    """
    How many people are on a team is the organiser's business, so nothing stops a third member
    from joining a two world race. This is also what allows handicap races.
    """
    await create_team(sa, team_room, 1235, "The Team")
    team = AsyncRaceTeam.get_by_id(1)

    await join_team(sa, team_room, 1236, team)
    result = await join_team(sa, team_room, 1237, team)

    assert [member.user_id for member in team.all_members()] == [1235, 1236, 1237]
    assert [t.member_count for t in result.teams] == [3]


@pytest.mark.usefixtures("_during_race")
async def test_join_team_already_started(sa, team_room):
    await create_team(sa, team_room, 1235, "The Team")
    team = AsyncRaceTeam.get_by_id(1)
    team.start_datetime = datetime.datetime(2020, 5, 11, tzinfo=datetime.UTC)
    team.save()

    with pytest.raises(error.InvalidActionError, match="This team has already started"):
        await join_team(sa, team_room, 1236, team)


@pytest.mark.usefixtures("_during_race")
async def test_join_team_invalid_code(sa, team_room):
    with pytest.raises(error.InvalidActionError, match="Invalid join code"):
        await room_api.join_team(sa, User.get_by_id(1236), team_room.id, "not-a-code")


@pytest.mark.usefixtures("_during_race")
async def test_join_team_code_of_another_room(sa, team_room, test_files_dir):
    await create_team(sa, team_room, 1235, "The Team")
    team = AsyncRaceTeam.get_by_id(1)

    other_room = AsyncRaceRoom.create(
        name="Other",
        visibility=MultiplayerSessionVisibility.VISIBLE,
        layout_description_json=team_room.layout_description_json,
        game_details_json=team_room.game_details_json,
        creator=User.get_by_id(1234),
        creation_date=team_room.creation_date,
        start_date=team_room.start_date,
        end_date=team_room.end_date,
        allow_pause=True,
    )

    assert team.captain_id is not None
    code = await room_api.get_team_join_code(User.get_by_id(team.captain_id), team_room.id)

    with pytest.raises(error.InvalidActionError, match="Invalid join code"):
        await room_api.join_team(sa, User.get_by_id(1236), other_room.id, code)


@pytest.mark.usefixtures("_during_race")
async def test_get_team_join_code_without_team(sa, team_room):
    with pytest.raises(error.NotAuthorizedForActionError):
        await room_api.get_team_join_code(User.get_by_id(1236), team_room.id)


@pytest.mark.usefixtures("_during_race")
async def test_leave_team_promotes_new_captain(sa, team_room):
    await create_team(sa, team_room, 1235, "The Team")
    team = AsyncRaceTeam.get_by_id(1)
    await join_team(sa, team_room, 1236, team)
    claim_world(team, 0, 1235)

    # Run
    result = await room_api.leave_team(sa, User.get_by_id(1235), team_room.id)

    # Assert
    team = AsyncRaceTeam.get_by_id(1)
    assert [member.user_id for member in team.all_members()] == [1236]
    assert team.captain_id == 1236

    # The world they claimed is released along with their access to the session
    session = team.session
    assert session is not None
    assert [membership.user_id for membership in session.members] == [1236]
    assert [assoc.user_id for world in session.get_ordered_worlds() for assoc in world.associations] == []

    assert result.self_team_id is None
    assert result.self_status == AsyncRaceRoomUserStatus.NOT_MEMBER

    assert [entry.as_entry().message for entry in team_room.audit_log] == [
        "Created team The Team.",
        "Joined team The Team.",
        "Left team The Team.",
        "Other Player is now the captain of team The Team.",
    ]


@pytest.mark.usefixtures("_during_race")
async def test_leave_team_last_member_deletes_team(sa, team_room):
    await create_team(sa, team_room, 1235, "The Team")
    session = AsyncRaceTeam.get_by_id(1).session
    assert session is not None
    session_id = session.id

    # Run
    await room_api.leave_team(sa, User.get_by_id(1235), team_room.id)

    # Assert
    assert list(AsyncRaceTeam.select()) == []
    assert list(AsyncRaceEntry.select()) == []
    assert MultiplayerSession.get_or_none(MultiplayerSession.id == session_id) is None


@pytest.mark.usefixtures("_during_race")
async def test_leave_team_after_exporting(sa, team_room):
    await create_team(sa, team_room, 1235, "The Team")
    entry = AsyncRaceEntry.entry_for(team_room, 1235)
    assert entry is not None
    entry.has_exported = True
    entry.save()

    with pytest.raises(error.InvalidActionError, match="Can't leave a team after exporting a game"):
        await room_api.leave_team(sa, User.get_by_id(1235), team_room.id)


@pytest.mark.usefixtures("_during_race")
async def test_leave_team_after_starting(sa, team_room):
    await create_team(sa, team_room, 1235, "The Team")
    team = AsyncRaceTeam.get_by_id(1)
    team.start_datetime = datetime.datetime(2020, 5, 11, tzinfo=datetime.UTC)
    team.save()

    with pytest.raises(error.InvalidActionError, match="Can't leave a team that has already started"):
        await room_api.leave_team(sa, User.get_by_id(1235), team_room.id)


@pytest.mark.usefixtures("_during_race")
async def test_leave_team_without_a_team(sa, team_room):
    with pytest.raises(error.InvalidActionError, match="You are not part of a team in this room"):
        await room_api.leave_team(sa, User.get_by_id(1236), team_room.id)


@pytest.mark.usefixtures("_during_race")
async def test_join_and_export_refused_in_team_room(sa, team_room, mocker: pytest_mock.MockFixture):
    mocker.patch("randovania.server.async_race.room_api._verify_authorization")

    with pytest.raises(error.InvalidActionError, match="This room is played in teams"):
        await room_api.join_and_export(sa, User.get_by_id(1235), team_room.id, "AuthToken", {})


async def _ready_team(sa: MagicMock, team_room: AsyncRaceRoom) -> AsyncRaceTeam:
    """A team of two with a world each, ready for its captain to start the timer."""
    await create_team(sa, team_room, 1235, "The Team")
    team = AsyncRaceTeam.get_by_id(1)
    await join_team(sa, team_room, 1236, team)
    claim_world(team, 0, 1235)
    claim_world(team, 1, 1236)
    return team


@pytest.mark.usefixtures("_during_race")
async def test_change_state_captain_only(sa, team_room):
    team = await _ready_team(sa, team_room)

    # A regular member can't move the shared timer
    with pytest.raises(error.NotAuthorizedForActionError):
        await change_state(sa, team_room, 1236, AsyncRaceRoomUserStatus.STARTED)

    assert AsyncRaceTeam.get_by_id(team.id).timer_status() == AsyncRaceRoomUserStatus.JOINED

    # The captain can
    result = await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    team = AsyncRaceTeam.get_by_id(team.id)
    assert team.timer_status() == AsyncRaceRoomUserStatus.STARTED
    assert team.start_datetime == datetime.datetime(2020, 5, 12, tzinfo=datetime.UTC)
    assert result.self_status == AsyncRaceRoomUserStatus.STARTED
    assert result.can_control_timer

    assert "Changed state of team The Team from joined to started" in [
        entry.as_entry().message for entry in team_room.audit_log
    ]


@pytest.mark.usefixtures("_during_race")
async def test_change_state_shared_by_whole_team(sa, team_room):
    """Every member sees the team's status, not one of their own."""
    team = await _ready_team(sa, team_room)

    await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    other = await AsyncRaceRoom.get_by_id(team_room.id).create_session_entry(sa, User.get_by_id(1236))
    assert other.self_status == AsyncRaceRoomUserStatus.STARTED
    assert other.self_team_id == team.id
    assert not other.can_control_timer


@pytest.mark.usefixtures("_during_race")
async def test_change_state_allows_a_team_of_any_size(sa, team_room):
    """
    Team sizes aren't restricted, so a single player covering both worlds of a two world race may
    start it just like a team of two would. This is what makes handicap races possible.
    """
    await create_team(sa, team_room, 1235, "Solo Team")
    team = AsyncRaceTeam.get_by_id(1)
    claim_world(team, 0, 1235)
    claim_world(team, 1, 1235)

    result = await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    assert result.self_status == AsyncRaceRoomUserStatus.STARTED
    assert AsyncRaceTeam.get_by_id(team.id).timer_status() == AsyncRaceRoomUserStatus.STARTED


@pytest.mark.usefixtures("_during_race")
async def test_change_state_needs_every_world_claimed(sa, team_room):
    await create_team(sa, team_room, 1235, "The Team")
    team = AsyncRaceTeam.get_by_id(1)
    await join_team(sa, team_room, 1236, team)
    claim_world(team, 0, 1235)

    with pytest.raises(error.InvalidActionError, match="Every world must be claimed before starting"):
        await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.STARTED)


@pytest.mark.usefixtures("_during_race")
async def test_change_state_needs_every_member_playing(sa, team_room):
    """With co-op a team can be larger than its world count, but nobody may sit idle."""
    team_room.allow_coop = True
    team_room.save()

    await create_team(sa, team_room, 1235, "The Team")
    team = AsyncRaceTeam.get_by_id(1)
    await join_team(sa, team_room, 1236, team)
    claim_world(team, 0, 1235)
    claim_world(team, 1, 1235)

    with pytest.raises(error.InvalidActionError, match="Every member must claim a world before starting"):
        await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.STARTED)


@pytest.mark.usefixtures("_during_race")
async def test_pause_uses_team_owned_pauses(sa, team_room):
    """A team's pauses hang off the team, so they count for whoever resumes the timer."""
    team = await _ready_team(sa, team_room)

    await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.STARTED)
    await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.PAUSED)

    pause = database.AsyncRaceEntryPause.get_by_id(1)
    assert pause.team_id == team.id
    assert pause.entry_id is None
    assert AsyncRaceTeam.get_by_id(team.id).timer_status() == AsyncRaceRoomUserStatus.PAUSED

    await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.STARTED)
    team = AsyncRaceTeam.get_by_id(team.id)
    assert team.timer_status() == AsyncRaceRoomUserStatus.STARTED
    assert team.total_pause_time() == datetime.timedelta(0)


@pytest.mark.usefixtures("_during_race")
async def test_submit_proof_is_shared_by_the_team(sa, team_room):
    """Proof belongs to the team's run, so any member can submit it and every member sees it."""
    team = await _ready_team(sa, team_room)
    team.start_datetime = datetime.datetime(2020, 5, 11, tzinfo=datetime.UTC)
    team.finish_datetime = datetime.datetime(2020, 5, 11, 2, tzinfo=datetime.UTC)
    team.save()

    await room_api.submit_proof(User.get_by_id(1236), team_room.id, "we did it", "https://example.com")

    assert await room_api.get_own_proof(User.get_by_id(1235), team_room.id) == (
        "we did it",
        "https://example.com",
    )


async def test_get_leaderboard_with_teams(sa, team_room, mocker: pytest_mock.MockFixture):
    now = mocker.patch("randovania.server.lib.datetime_now")
    now.return_value = datetime.datetime(2020, 5, 12, tzinfo=datetime.UTC)

    await create_team(sa, team_room, 1235, "Fast Team")
    fast = AsyncRaceTeam.get_by_id(1)
    await join_team(sa, team_room, 1236, fast)

    await create_team(sa, team_room, 1237, "Slow Team")
    slow = AsyncRaceTeam.get_by_id(2)

    fast.start_datetime = datetime.datetime(2020, 5, 11, tzinfo=datetime.UTC)
    fast.finish_datetime = datetime.datetime(2020, 5, 11, 1, tzinfo=datetime.UTC)
    fast.save()

    slow.start_datetime = datetime.datetime(2020, 5, 11, tzinfo=datetime.UTC)
    slow.forfeit = True
    slow.save()

    # Run
    now.return_value = datetime.datetime(2021, 5, 12, tzinfo=datetime.UTC)
    result = await room_api.get_leaderboard(sa, User.get_by_id(1234), team_room.id, "")

    # Assert
    assert result == RaceRoomLeaderboard(
        entries=[
            RaceRoomLeaderboardEntry(
                display_name="Fast Team",
                time=datetime.timedelta(hours=1),
                members=[RandovaniaUser(1235, "The Player"), RandovaniaUser(1236, "Other Player")],
            ),
            RaceRoomLeaderboardEntry(
                display_name="Slow Team", time=None, members=[RandovaniaUser(1237, "Third Player")]
            ),
        ],
        uses_teams=True,
    )


@pytest.mark.usefixtures("_during_race")
async def test_admin_data_lists_teams(sa, team_room):
    await create_team(sa, team_room, 1235, "The Team")
    team = AsyncRaceTeam.get_by_id(1)
    await join_team(sa, team_room, 1236, team)

    # Run
    result = await room_api.admin_get_admin_data(User.get_by_id(1234), team_room.id)

    # Assert
    assert result.model_dump(mode="json") == {
        "users": [
            {
                "user": {"id": 1235, "name": "The Player"},
                "team_id": 1,
                "team_name": "The Team",
                "members": [{"id": 1235, "name": "The Player"}, {"id": 1236, "name": "Other Player"}],
                "join_date": ANY,
                "start_date": None,
                "finish_date": None,
                "forfeit": False,
                "submission_notes": "",
                "proof_url": "",
                "pauses": [],
            }
        ]
    }


@pytest.mark.usefixtures("_during_race")
async def test_admin_update_entries_for_a_team(sa, team_room):
    await create_team(sa, team_room, 1235, "The Team")
    team = AsyncRaceTeam.get_by_id(1)

    new_entries = [
        AsyncRaceEntryData(
            user=None,
            team_id=team.id,
            team_name="The Team",
            members=[],
            join_date=datetime.datetime(2020, 5, 6, tzinfo=datetime.UTC),
            start_date=datetime.datetime(2020, 5, 11, tzinfo=datetime.UTC),
            finish_date=datetime.datetime(2020, 5, 11, 3, tzinfo=datetime.UTC),
            forfeit=False,
            pauses=[],
            submission_notes="checked",
            proof_url="https://example.com",
        )
    ]

    # Run
    await room_api.admin_update_entries(sa, User.get_by_id(1234), team_room.id, new_entries)

    # Assert
    team = AsyncRaceTeam.get_by_id(team.id)
    assert team.elapsed_time() == datetime.timedelta(hours=3)
    assert team.submission_notes == "checked"
    assert team.proof_url == "https://example.com"

    assert "Modified entries for ['The Team']." in [entry.as_entry().message for entry in team_room.audit_log]


@pytest.mark.usefixtures("_during_race")
async def test_admin_update_entries_unknown_team(sa, team_room):
    new_entries = [
        AsyncRaceEntryData(
            user=None,
            team_id=1234,
            team_name="Nowhere",
            members=[],
            join_date=datetime.datetime(2020, 5, 6, tzinfo=datetime.UTC),
            start_date=None,
            finish_date=None,
            forfeit=False,
            pauses=[],
            submission_notes="",
            proof_url="",
        )
    ]

    with pytest.raises(error.InvalidActionError, match="Nowhere is not a member of this room"):
        await room_api.admin_update_entries(sa, User.get_by_id(1234), team_room.id, new_entries)


@pytest.mark.usefixtures("_during_race")
async def test_create_session_entry_hides_other_teams_sessions(sa, team_room):
    """A team's session id is what lets you open it, so only its own members get one."""
    await create_team(sa, team_room, 1235, "First")
    await create_team(sa, team_room, 1236, "Second")

    entry = await AsyncRaceRoom.get_by_id(team_room.id).create_session_entry(sa, User.get_by_id(1235))
    assert [(team.name, team.session_id is not None) for team in entry.teams] == [("First", True), ("Second", False)]
    own_team = entry.self_team
    assert own_team is not None
    assert own_team.name == "First"

    # The room's creator checks every team for cheating, so they see all of them
    admin_entry = await AsyncRaceRoom.get_by_id(team_room.id).create_session_entry(sa, User.get_by_id(1234))
    assert [(team.name, team.session_id is not None) for team in admin_entry.teams] == [
        ("First", True),
        ("Second", True),
    ]
    assert admin_entry.self_team is None


@pytest.mark.usefixtures("_during_race")
async def test_create_session_entry_reports_claimed_worlds(sa, team_room):
    await create_team(sa, team_room, 1235, "The Team")
    team = AsyncRaceTeam.get_by_id(1)
    await join_team(sa, team_room, 1236, team)
    claim_world(team, 0, 1235)

    entry = await AsyncRaceRoom.get_by_id(team_room.id).create_session_entry(sa, User.get_by_id(1235))
    own_team = entry.self_team
    assert own_team is not None

    assert [(world.order, [user.id for user in world.claimed_by]) for world in own_team.worlds] == [
        (0, [1235]),
        (1, []),
    ]
    assert [world.order for world in own_team.worlds_for(1235)] == [0]
    assert [world.order for world in own_team.unclaimed_worlds] == [1]


@pytest.mark.usefixtures("_during_race")
async def test_emit_async_room_update_reaches_whole_team(sa, team_room, mocker: pytest_mock.MockFixture):
    """The timer is shared, so a change by one member has to be pushed to all of them."""
    mock_emit = mocker.patch("randovania.network_common.signals.client_signals.AsyncRaceRoomUpdate.emit")
    mock_emit.return_value = AsyncMock()

    await create_team(sa, team_room, 1235, "The Team")
    team = AsyncRaceTeam.get_by_id(1)
    await join_team(sa, team_room, 1236, team)

    # Run
    await room_api.emit_async_room_update(sa, AsyncRaceRoom.get_by_id(team_room.id), User.get_by_id(1235))

    # Assert
    assert [call.kwargs["to"] for call in mock_emit.call_args_list] == [
        "async-race-1-1235",
        "async-race-1-1236",
    ]


def _settings(**kwargs) -> AsyncRaceSettings:
    defaults = {
        "name": "Debug",
        "password": None,
        "start_date": datetime.datetime(2020, 5, 10, tzinfo=datetime.UTC),
        "end_date": datetime.datetime(2020, 6, 10, tzinfo=datetime.UTC),
        "visibility": MultiplayerSessionVisibility.VISIBLE,
        "allow_pause": True,
    }
    return AsyncRaceSettings(**(defaults | kwargs))


@pytest.mark.usefixtures("_during_race")
async def test_change_room_settings_locks_the_timer_mode(sa, team_room):
    """How a team is timed shapes the teams that already exist, so it can't move under them."""
    await create_team(sa, team_room, 1235, "The Team")

    with pytest.raises(error.InvalidActionError, match="Can't change how the timer is kept"):
        await room_api.change_room_settings(sa, User.get_by_id(1234), team_room.id, _settings(shared_team_timer=False))


@pytest.mark.usefixtures("_during_race")
async def test_change_room_settings_keeps_team_settings(sa, team_room):
    """Settings that don't decide the shape of a team may still be changed after people joined."""
    await create_team(sa, team_room, 1235, "The Team")

    result = await room_api.change_room_settings(
        sa, User.get_by_id(1234), team_room.id, _settings(name="Renamed", allow_abandon_worlds=True)
    )

    assert result.name == "Renamed"
    assert result.allow_abandon_worlds
    assert result.uses_teams


async def test_create_room_multiworld_needs_teams(sa, clean_database, test_files_dir):
    """A layout with more than one world is played in teams, of whatever size the organiser wants."""
    from randovania.layout.layout_description import LayoutDescription

    User.create(id=1234, name="The Name")
    user = User.get_by_id(1234)

    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "prime1_and_2_multi.rdvgame"))
    settings = _settings(
        name="TheRoom",
        start_date=datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2021, 1, 1, tzinfo=datetime.UTC),
    )

    result = await room_api.create_room(sa, user, description.as_binary(), settings)

    assert result.world_count == 2
    assert result.uses_teams
    assert result.shared_team_timer


async def test_create_room_coop_needs_teams(sa, clean_database, test_files_dir):
    """A single world race is played alone, unless co-op turns it into a team one."""
    from randovania.layout.layout_description import LayoutDescription

    User.create(id=1234, name="The Name")
    user = User.get_by_id(1234)

    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "prime2_seed_b.rdvgame"))
    settings = _settings(
        name="TheRoom",
        start_date=datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2021, 1, 1, tzinfo=datetime.UTC),
    )

    solo = await room_api.create_room(sa, user, description.as_binary(), settings)
    assert solo.world_count == 1
    assert not solo.uses_teams

    coop = await room_api.create_room(sa, user, description.as_binary(), _settings_with_coop(settings))
    assert coop.world_count == 1
    assert coop.uses_teams


def _settings_with_coop(settings: AsyncRaceSettings) -> AsyncRaceSettings:
    return settings.model_copy(update={"allow_coop": True})


# --- Rooms that accumulate each member's time instead of sharing one timer ---


@pytest.fixture
def accumulating_room(team_room) -> AsyncRaceRoom:
    team_room.shared_team_timer = False
    team_room.save()
    return team_room


@pytest.mark.usefixtures("_during_race")
async def test_accumulated_captain_starts_every_member(sa, accumulating_room):
    """The captain still starts the race, and doing so starts every member's own timer."""
    team = await _ready_team(sa, accumulating_room)

    # A regular member still can't start the race
    # NotAuthorizedForActionError carries its reason in the payload, not in str()
    with pytest.raises(error.NotAuthorizedForActionError):
        await change_state(sa, accumulating_room, 1236, AsyncRaceRoomUserStatus.STARTED)

    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    now = datetime.datetime(2020, 5, 12, tzinfo=datetime.UTC)
    team = AsyncRaceTeam.get_by_id(team.id)
    assert team.start_datetime == now
    assert [member.start_datetime for member in team.all_members()] == [now, now]
    assert team.timer_status() == AsyncRaceRoomUserStatus.STARTED


@pytest.mark.usefixtures("_during_race")
async def test_accumulated_members_drive_their_own_timer(sa, accumulating_room):
    """Once started, every member finishes on their own without touching anyone else's timer."""
    team = await _ready_team(sa, accumulating_room)
    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    result = await change_state(sa, accumulating_room, 1236, AsyncRaceRoomUserStatus.FINISHED)
    assert result.self_status == AsyncRaceRoomUserStatus.FINISHED
    assert result.can_control_timer

    team = AsyncRaceTeam.get_by_id(team.id)
    assert [member.timer_status() for member in team.all_members()] == [
        AsyncRaceRoomUserStatus.STARTED,
        AsyncRaceRoomUserStatus.FINISHED,
    ]
    # The team is only done once everyone is
    assert team.timer_status() == AsyncRaceRoomUserStatus.STARTED

    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.FINISHED)
    assert AsyncRaceTeam.get_by_id(team.id).timer_status() == AsyncRaceRoomUserStatus.FINISHED


@pytest.mark.usefixtures("_during_race")
async def test_accumulated_time_is_the_sum_of_the_members(sa, accumulating_room):
    team = await _ready_team(sa, accumulating_room)
    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    team = AsyncRaceTeam.get_by_id(team.id)
    first, second = team.all_members()

    finish_run(first, hours=1)
    finish_run(second, hours=2)

    assert AsyncRaceTeam.get_by_id(team.id).elapsed_time() == datetime.timedelta(hours=3)


@pytest.mark.usefixtures("_during_race")
async def test_accumulated_undoing_the_start_resets_the_members(sa, accumulating_room):
    team = await _ready_team(sa, accumulating_room)
    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.STARTED)
    await change_state(sa, accumulating_room, 1236, AsyncRaceRoomUserStatus.FINISHED)

    # Only the captain may undo the start, and it puts the whole team back to joined
    with pytest.raises(error.NotAuthorizedForActionError):
        await change_state(sa, accumulating_room, 1236, AsyncRaceRoomUserStatus.JOINED)

    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.JOINED)

    team = AsyncRaceTeam.get_by_id(team.id)
    assert team.timer_status() == AsyncRaceRoomUserStatus.JOINED
    assert [member.timer_status() for member in team.all_members()] == [
        AsyncRaceRoomUserStatus.JOINED,
        AsyncRaceRoomUserStatus.JOINED,
    ]


@pytest.mark.usefixtures("_during_race")
async def test_accumulated_members_are_reported_individually(sa, accumulating_room):
    """Each member's own state reaches the client, since they are all running separate timers."""
    await _ready_team(sa, accumulating_room)
    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.STARTED)
    await change_state(sa, accumulating_room, 1236, AsyncRaceRoomUserStatus.FINISHED)

    entry = await AsyncRaceRoom.get_by_id(accumulating_room.id).create_session_entry(sa, User.get_by_id(1236))
    assert not entry.shared_team_timer
    own_team = entry.self_team
    assert own_team is not None
    assert [(member.user.id, member.status) for member in own_team.members] == [
        (1235, AsyncRaceRoomUserStatus.STARTED),
        (1236, AsyncRaceRoomUserStatus.FINISHED),
    ]


@pytest.mark.usefixtures("_during_race")
async def test_accumulated_undoing_the_start_after_everyone_finished(sa, accumulating_room):
    """The team reads as finished once all its members are, but the captain can still undo."""
    team = await _ready_team(sa, accumulating_room)
    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.STARTED)
    await change_state(sa, accumulating_room, 1236, AsyncRaceRoomUserStatus.FINISHED)
    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.FINISHED)

    assert AsyncRaceTeam.get_by_id(team.id).timer_status() == AsyncRaceRoomUserStatus.FINISHED

    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.JOINED)

    team = AsyncRaceTeam.get_by_id(team.id)
    assert team.timer_status() == AsyncRaceRoomUserStatus.JOINED
    assert team.start_datetime is None
    assert [member.timer_status() for member in team.all_members()] == [
        AsyncRaceRoomUserStatus.JOINED,
        AsyncRaceRoomUserStatus.JOINED,
    ]


@pytest.mark.usefixtures("_during_race")
async def test_accumulated_forfeit_is_the_whole_teams(sa, accumulating_room):
    """
    Half a team giving up means nothing, so forfeiting stays the captain's even when every member
    otherwise runs their own timer.
    """
    team = await _ready_team(sa, accumulating_room)
    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    # A regular member can't forfeit, for themselves or anyone else
    with pytest.raises(error.NotAuthorizedForActionError):
        await change_state(sa, accumulating_room, 1236, AsyncRaceRoomUserStatus.FORFEITED)

    assert AsyncRaceTeam.get_by_id(team.id).timer_status() == AsyncRaceRoomUserStatus.STARTED

    # The captain forfeits for everyone
    result = await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.FORFEITED)

    team = AsyncRaceTeam.get_by_id(team.id)
    assert team.forfeit
    assert team.timer_status() == AsyncRaceRoomUserStatus.FORFEITED
    assert result.self_status == AsyncRaceRoomUserStatus.FORFEITED

    # And every member is shown as forfeited, whatever their own timer says
    other = await AsyncRaceRoom.get_by_id(accumulating_room.id).create_session_entry(sa, User.get_by_id(1236))
    assert other.self_status == AsyncRaceRoomUserStatus.FORFEITED
    assert not other.can_control_team


@pytest.mark.usefixtures("_during_race")
async def test_accumulated_undoing_a_forfeit_is_the_captains(sa, accumulating_room):
    team = await _ready_team(sa, accumulating_room)
    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.STARTED)
    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.FORFEITED)

    # While the team is forfeited, a member can't move anything back
    with pytest.raises(error.NotAuthorizedForActionError):
        await change_state(sa, accumulating_room, 1236, AsyncRaceRoomUserStatus.STARTED)

    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    team = AsyncRaceTeam.get_by_id(team.id)
    assert not team.forfeit
    assert team.timer_status() == AsyncRaceRoomUserStatus.STARTED


@pytest.mark.usefixtures("_during_race")
async def test_accumulated_forfeit_after_a_member_finished(sa, accumulating_room):
    """A team can still give up once part of it is done; the whole run stops counting."""
    team = await _ready_team(sa, accumulating_room)
    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.STARTED)
    await change_state(sa, accumulating_room, 1236, AsyncRaceRoomUserStatus.FINISHED)

    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.FORFEITED)

    assert AsyncRaceTeam.get_by_id(team.id).timer_status() == AsyncRaceRoomUserStatus.FORFEITED


# --- Reporting the user's own final time ---


@pytest.mark.usefixtures("_during_race")
async def test_self_time_shared_is_the_teams_timer(sa, team_room):
    """A shared timer belongs to the team, so every member is told the team's time."""
    team = await _ready_team(sa, team_room)
    await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    # Nothing to report while the run is still going
    for user_id in (1235, 1236):
        entry = await AsyncRaceRoom.get_by_id(team_room.id).create_session_entry(sa, User.get_by_id(user_id))
        assert entry.self_time is None

    team = AsyncRaceTeam.get_by_id(team.id)
    finish_run(team, hours=1, minutes=30)

    # The captain and a regular member are told the same thing
    for user_id in (1235, 1236):
        entry = await AsyncRaceRoom.get_by_id(team_room.id).create_session_entry(sa, User.get_by_id(user_id))
        assert entry.self_time == datetime.timedelta(hours=1, minutes=30)


@pytest.mark.usefixtures("_during_race")
async def test_self_time_accumulated_waits_for_every_member(sa, accumulating_room):
    """
    An accumulating team's time is only meaningful once everyone is done: reporting it earlier
    would show a sum that is still growing.
    """
    team = await _ready_team(sa, accumulating_room)
    await change_state(sa, accumulating_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    team = AsyncRaceTeam.get_by_id(team.id)
    first, second = team.all_members()
    finish_run(first, hours=1)

    # One member down, so the sum isn't final yet
    entry = await AsyncRaceRoom.get_by_id(accumulating_room.id).create_session_entry(sa, User.get_by_id(1235))
    assert entry.self_status == AsyncRaceRoomUserStatus.FINISHED
    assert entry.self_time is None

    finish_run(second, hours=2)

    for user_id in (1235, 1236):
        entry = await AsyncRaceRoom.get_by_id(accumulating_room.id).create_session_entry(sa, User.get_by_id(user_id))
        assert entry.self_time == datetime.timedelta(hours=3)


@pytest.mark.usefixtures("_during_race")
async def test_self_time_is_not_reported_for_a_forfeit(sa, team_room):
    """Giving up leaves no time, exactly as the leaderboard reports it."""
    team = await _ready_team(sa, team_room)
    await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    team = AsyncRaceTeam.get_by_id(team.id)
    finish_run(team, hours=1)
    await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.FORFEITED)

    entry = await AsyncRaceRoom.get_by_id(team_room.id).create_session_entry(sa, User.get_by_id(1236))
    assert entry.self_status == AsyncRaceRoomUserStatus.FORFEITED
    assert entry.self_time is None


@pytest.mark.usefixtures("_during_race")
async def test_self_time_says_nothing_about_other_teams(sa, team_room):
    """A rival finishing doesn't give the user a time; only their own run does."""
    await _ready_team(sa, team_room)
    await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    await create_team(sa, team_room, 1237, "The Others")
    other = AsyncRaceTeam.get_by_id(2)
    claim_world(other, 0, 1237)
    claim_world(other, 1, 1237)
    await change_state(sa, team_room, 1237, AsyncRaceRoomUserStatus.STARTED)
    other = AsyncRaceTeam.get_by_id(other.id)
    finish_run(other, hours=1)

    entry = await AsyncRaceRoom.get_by_id(team_room.id).create_session_entry(sa, User.get_by_id(1235))
    assert entry.self_time is None


@pytest.mark.usefixtures("_during_race")
async def test_other_teams_progress_is_withheld(sa, team_room):
    """
    How a rival team is doing is the leaderboard's to reveal. Who is on it stays public: that is
    what stops a user joining a team they're already racing against.
    """
    await _ready_team(sa, team_room)
    await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    await create_team(sa, team_room, 1237, "The Others")

    entry = await AsyncRaceRoom.get_by_id(team_room.id).create_session_entry(sa, User.get_by_id(1237))
    own, rival = (team for team in sorted(entry.teams, key=lambda team: team.id != entry.self_team_id))

    assert own.name == "The Others"
    assert own.status == AsyncRaceRoomUserStatus.JOINED
    assert [member.status for member in own.members] == [AsyncRaceRoomUserStatus.JOINED]

    # The team that started says nothing about it
    assert rival.name == "The Team"
    assert rival.status is None
    assert [member.user.name for member in rival.members] == ["The Player", "Other Player"]
    assert [member.status for member in rival.members] == [None, None]
    assert [member.time for member in rival.members] == [None, None]


async def test_every_teams_progress_after_the_race(sa, team_room, mocker: pytest_mock.MockFixture):
    """Once the race is over there is nothing left to withhold: the leaderboard is open too."""
    mocker.patch(
        "randovania.server.lib.datetime_now",
        return_value=datetime.datetime(2020, 5, 12, tzinfo=datetime.UTC),
    )
    await _ready_team(sa, team_room)
    await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.STARTED)
    await create_team(sa, team_room, 1237, "The Others")

    mocker.patch(
        "randovania.server.lib.datetime_now",
        return_value=datetime.datetime(2020, 7, 1, tzinfo=datetime.UTC),
    )

    entry = await AsyncRaceRoom.get_by_id(team_room.id).create_session_entry(sa, User.get_by_id(1237))
    assert entry.race_status == AsyncRaceRoomRaceStatus.FINISHED
    assert [team.status for team in entry.teams] == [
        AsyncRaceRoomUserStatus.STARTED,
        AsyncRaceRoomUserStatus.JOINED,
    ]


@pytest.mark.usefixtures("_during_race")
async def test_other_teams_progress_is_withheld_from_the_admin_too(sa, team_room):
    """The creator reads the whole picture through the admin data, not through the room."""
    await _ready_team(sa, team_room)
    await change_state(sa, team_room, 1235, AsyncRaceRoomUserStatus.STARTED)

    entry = await AsyncRaceRoom.get_by_id(team_room.id).create_session_entry(sa, User.get_by_id(1234))
    assert entry.is_admin
    assert [team.status for team in entry.teams] == [None]
    # They can still reach every team's session, which is what running the room takes
    assert [team.session_id is not None for team in entry.teams] == [True]
