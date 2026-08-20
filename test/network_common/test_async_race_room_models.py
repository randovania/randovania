from __future__ import annotations

import datetime
import uuid

import pytest

from randovania.network_common.async_race_room import (
    AsyncRaceEntryData,
    AsyncRaceRoomEntry,
    AsyncRaceRoomRaceStatus,
    AsyncRaceRoomUserStatus,
    AsyncRaceTeamEntry,
    AsyncRaceTeamMember,
    AsyncRaceWorldEntry,
    race_uses_teams,
)
from randovania.network_common.game_details import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.network_common.user import RandovaniaUser


@pytest.mark.parametrize(
    ("world_count", "allow_coop", "expected"),
    [
        # One player, one world: nothing to host
        (1, False, False),
        # More than one world needs a session for the items to travel through
        (2, False, True),
        (3, False, True),
        # And so does co-op, where a world is shared rather than one per player
        (1, True, True),
        (2, True, True),
    ],
)
def test_race_uses_teams(world_count: int, allow_coop: bool, expected: bool):
    assert race_uses_teams(world_count, allow_coop) is expected


def _room(**changes) -> AsyncRaceRoomEntry:
    changes.setdefault("self_status", AsyncRaceRoomUserStatus.NOT_MEMBER)
    return AsyncRaceRoomEntry(
        id=1,
        name="Room",
        creator="TheCreator",
        creation_date=datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
        start_date=datetime.datetime(2020, 2, 1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2020, 3, 1, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        race_status=AsyncRaceRoomRaceStatus.ACTIVE,
        auth_token="Token",
        game_details=GameDetails(seed_hash="HASH", word_hash="Words", spoiler=False),
        presets_raw=[],
        is_admin=False,
        allow_pause=False,
        **changes,
    )


def _team(**changes) -> AsyncRaceTeamEntry:
    return AsyncRaceTeamEntry(
        id=1,
        name="The Team",
        status=AsyncRaceRoomUserStatus.JOINED,
        members=[
            AsyncRaceTeamMember(user=RandovaniaUser(10, "Alice")),
            AsyncRaceTeamMember(user=RandovaniaUser(11, "Bob")),
        ],
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
        **changes,
    )


def test_solo_racer_always_controls_their_timer():
    room = _room()

    assert not room.uses_teams
    assert not room.is_multiworld
    assert room.can_control_timer
    assert room.self_team is None


@pytest.mark.parametrize("is_captain", [False, True])
def test_shared_team_timer_belongs_to_the_captain(is_captain: bool):
    room = _room(world_count=2, teams=[_team()], self_team_id=1, self_is_captain=is_captain)

    assert room.uses_teams
    assert room.is_multiworld
    assert room.shared_team_timer
    assert room.can_control_timer is is_captain
    assert room.self_team is room.teams[0]


@pytest.mark.parametrize(
    ("self_status", "expected"),
    [
        # The captain starts the race for everyone, so a member can do nothing until they have
        (AsyncRaceRoomUserStatus.JOINED, False),
        (AsyncRaceRoomUserStatus.STARTED, True),
        (AsyncRaceRoomUserStatus.PAUSED, True),
        (AsyncRaceRoomUserStatus.FINISHED, True),
    ],
)
def test_accumulated_timer_is_the_members_own_once_started(self_status: AsyncRaceRoomUserStatus, expected: bool):
    room = _room(
        world_count=2,
        teams=[_team()],
        self_team_id=1,
        self_is_captain=False,
        shared_team_timer=False,
        self_status=self_status,
    )

    assert room.uses_teams
    assert not room.shared_team_timer
    assert room.can_control_timer is expected


def test_accumulated_timer_captain_always_controls():
    room = _room(
        world_count=2,
        teams=[_team()],
        self_team_id=1,
        self_is_captain=True,
        shared_team_timer=False,
        self_status=AsyncRaceRoomUserStatus.JOINED,
    )

    assert room.can_control_timer


def test_coop_single_world_uses_teams():
    """One world is still played by a team once co-op is on, mirroring WorldsConfiguration."""
    room = _room(world_count=1, allow_coop=True, teams=[_team()], self_team_id=1)

    assert room.uses_teams
    assert not room.is_multiworld


def test_self_team_of_an_unknown_id():
    """A stale team id from a room that moved on shouldn't be reported as your team."""
    room = _room(world_count=2, teams=[_team()], self_team_id=99)

    assert room.self_team is None


def test_team_world_lookups():
    team = _team()

    assert team.member_count == 2
    assert [user.id for user in team.member_users] == [10, 11]
    assert team.member_for(10).user.name == "Alice"
    assert team.member_for(99) is None
    assert [world.order for world in team.worlds_for(10)] == [0]
    assert team.worlds_for(11) == []
    assert [world.order for world in team.unclaimed_worlds] == [1]
    assert team.worlds[0].is_claimed_by(10)
    assert not team.worlds[0].is_claimed_by(11)


def _entry_data(**changes) -> AsyncRaceEntryData:
    changes.setdefault("user", RandovaniaUser(10, "Alice"))
    return AsyncRaceEntryData(
        join_date=datetime.datetime(2020, 2, 2, tzinfo=datetime.UTC),
        start_date=None,
        finish_date=None,
        forfeit=False,
        pauses=[],
        submission_notes="",
        proof_url="",
        **changes,
    )


def test_entry_display_name_prefers_the_team():
    """Admin views name a participant after its team when it has one, and after the user if not."""
    assert _entry_data().display_name == "Alice"
    assert _entry_data(team_name="The Team").display_name == "The Team"
    assert _entry_data(user=None).display_name == "<unknown>"


def test_solo_racer_controls_their_own_team_moves():
    assert _room().can_control_team


@pytest.mark.parametrize("shared_team_timer", [False, True])
@pytest.mark.parametrize("is_captain", [False, True])
def test_team_moves_are_always_the_captains(is_captain: bool, shared_team_timer: bool):
    """Starting and forfeiting belong to the captain however the room is timed."""
    room = _room(
        world_count=2,
        teams=[_team()],
        self_team_id=1,
        self_is_captain=is_captain,
        shared_team_timer=shared_team_timer,
        self_status=AsyncRaceRoomUserStatus.STARTED,
    )

    assert room.can_control_team is is_captain
