from __future__ import annotations

import uuid

import pytest

from randovania.network_common import error
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server import database
from randovania.server.async_race import team_session
from randovania.server.database import AsyncRaceTeam, User, World, WorldUserAssociation


@pytest.fixture
def team(team_room) -> AsyncRaceTeam:
    """A team of one, with the hidden session that hosts its multiworld."""
    new_team = AsyncRaceTeam.create(room=team_room, name="The Team", captain=User.get_by_id(1235))
    session = team_session.create_session_for_team(team_room, new_team)
    team_session.add_member(session, User.get_by_id(1235))
    database.AsyncRaceEntry.create(room=team_room, user=User.get_by_id(1235), team=new_team)
    return new_team


def test_create_session_for_team(team_room, team):
    session = team.session

    assert session is not None
    assert session.name == "Debug - The Team"
    assert session.password is None
    assert session.visibility == MultiplayerSessionVisibility.HIDDEN
    assert session.creator_id == team_room.creator_id
    assert session.is_race_session
    assert session.get_race_team().id == team.id

    worlds = session.get_ordered_worlds()
    assert [(world.name, world.order) for world in worlds] == [("World 1", 0), ("World 2", 1)]
    assert session.layout_description.as_binary() == team_room.layout_description.as_binary()

    assert session.allow_everyone_claim_world
    assert session.allow_coop == team_room.allow_coop
    assert session.allow_abandon_worlds == team_room.allow_abandon_worlds


def test_apply_room_settings(team_room, team):
    team_room.allow_coop = True
    team_room.allow_abandon_worlds = True
    team_room.save()

    # Run
    team_session.apply_room_settings(team_room)

    # Assert
    session = team.session
    assert session.allow_coop
    assert session.allow_abandon_worlds


def test_apply_room_settings_refuses_disabling_coop_in_use(team_room, team):
    team_room.allow_coop = True
    team_room.save()
    team_session.apply_room_settings(team_room)

    world = team.session.get_ordered_worlds()[0]
    WorldUserAssociation.create(world=world, user=User.get_by_id(1235))
    WorldUserAssociation.create(world=world, user=User.get_by_id(1236))

    team_room.allow_coop = False
    team_room.save()

    with pytest.raises(error.InvalidActionError, match="Can't disable co-op: World 1 of team The Team"):
        team_session.apply_room_settings(team_room)


def test_apply_room_settings_refuses_disabling_abandon_in_use(team_room, team):
    team_room.allow_abandon_worlds = True
    team_room.save()
    team_session.apply_room_settings(team_room)

    world = team.session.get_ordered_worlds()[1]
    world.abandoned = True
    world.save()

    team_room.allow_abandon_worlds = False
    team_room.save()

    with pytest.raises(error.InvalidActionError, match="Can't disable abandoning: World 2 of team The Team"):
        team_session.apply_room_settings(team_room)


def test_add_member_is_idempotent(team_room, team):
    session = team.session
    team_session.add_member(session, User.get_by_id(1236))
    team_session.add_member(session, User.get_by_id(1236))

    memberships = list(database.MultiplayerMembership.select().where(database.MultiplayerMembership.session == session))
    assert sorted(membership.user_id for membership in memberships) == [1235, 1236]
    assert not any(membership.admin for membership in memberships)


def test_remove_member_releases_worlds(team_room, team):
    session = team.session
    team_session.add_member(session, User.get_by_id(1236))

    world_1, world_2 = session.get_ordered_worlds()
    WorldUserAssociation.create(world=world_1, user=User.get_by_id(1235))
    WorldUserAssociation.create(world=world_2, user=User.get_by_id(1236))

    # Run
    team_session.remove_member(session, User.get_by_id(1236))

    # Assert
    assert [membership.user_id for membership in session.members] == [1235]
    assert [assoc.user_id for world in session.get_ordered_worlds() for assoc in world.associations] == [1235]


def test_all_worlds_claimed(team_room, team):
    session = team.session
    world_1, world_2 = session.get_ordered_worlds()

    assert not team_session.all_worlds_claimed(session)

    WorldUserAssociation.create(world=world_1, user=User.get_by_id(1235))
    assert not team_session.all_worlds_claimed(session)

    WorldUserAssociation.create(world=world_2, user=User.get_by_id(1235))
    assert team_session.all_worlds_claimed(session)


def test_get_world_for(team_room, team):
    session = team.session
    world = session.get_ordered_worlds()[0]

    assert team_session.get_world_for(session, world.uuid).id == world.id


def test_get_world_for_another_session(team_room, team):
    """A world uuid is only usable in the session that owns it, even for a valid one."""
    other_session = database.MultiplayerSession.create(
        name="Elsewhere",
        visibility=MultiplayerSessionVisibility.VISIBLE,
        creator=User.get_by_id(1234),
    )
    other_world = World.create(session=other_session, name="World 1", preset="{}", order=0, uuid=uuid.uuid4())

    with pytest.raises(error.WorldDoesNotExistError):
        team_session.get_world_for(team.session, other_world.uuid)


def test_team_helpers(team_room, team):
    """
    `unclaimed_worlds` and `members_without_world` gate a team from starting. How many members
    a team has is not one of the gates: that is up to the organiser.
    """
    assert team.is_captain(User.get_by_id(1235))
    assert not team.is_captain(User.get_by_id(1236))

    session = team.session
    team_session.add_member(session, User.get_by_id(1236))
    database.AsyncRaceEntry.create(room=team_room, user=User.get_by_id(1236), team=team)

    world_1, world_2 = session.get_ordered_worlds()
    assert [world.id for world in team.unclaimed_worlds()] == [world_1.id, world_2.id]
    assert [entry.user_id for entry in team.members_without_world()] == [1235, 1236]

    WorldUserAssociation.create(world=world_1, user=User.get_by_id(1235))
    assert [world.id for world in team.unclaimed_worlds()] == [world_2.id]
    assert [entry.user_id for entry in team.members_without_world()] == [1236]


def test_promote_new_captain_without_members(team_room, team):
    database.AsyncRaceEntry.delete().where(database.AsyncRaceEntry.team == team).execute()

    team.promote_new_captain()

    assert AsyncRaceTeam.get_by_id(team.id).captain_id is None
