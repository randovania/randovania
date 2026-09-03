from __future__ import annotations

import typing

from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common import error
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server import database

if typing.TYPE_CHECKING:
    import uuid

    from randovania.server.database import AsyncRaceRoom, AsyncRaceTeam, MultiplayerSession, User, World


def create_session_for_team(room: AsyncRaceRoom, team: AsyncRaceTeam) -> MultiplayerSession:
    """
    Creates the hidden MultiplayerSession that hosts one team's multiworld.
    """
    layout = room.layout_description

    with database.db.atomic():
        session = database.MultiplayerSession.create(
            name=f"{room.name} - {team.name}",
            password=None,
            visibility=MultiplayerSessionVisibility.HIDDEN,
            creator=room.creator,
            race_team=team,
            allow_coop=room.allow_coop,
            allow_abandon_worlds=room.allow_abandon_worlds,
            allow_everyone_claim_world=True,
        )

        for order, preset in enumerate(layout.all_presets):
            database.World.create_for(
                session=session,
                name=f"World {order + 1}",
                preset=VersionedPreset.with_preset(preset),
                order=order,
            )

        session.layout_description = layout
        session.save()

    return session


def apply_room_settings(room: AsyncRaceRoom) -> None:
    """
    Pushes the room's session settings onto every team, so that changing them applies to teams
    that already exist rather than only to the ones created afterwards.
    """
    with database.db.atomic():
        for team in database.AsyncRaceTeam.select().where(database.AsyncRaceTeam.room == room):
            session = team.session
            if session is None:
                continue

            if not room.allow_coop:
                for world in session.worlds:
                    if len(list(world.associations)) >= 2:
                        raise error.InvalidActionError(
                            f"Can't disable co-op: {world.name} of team {team.name} has several players"
                        )

            if not room.allow_abandon_worlds:
                for world in session.worlds:
                    if world.abandoned:
                        raise error.InvalidActionError(
                            f"Can't disable abandoning: {world.name} of team {team.name} is abandoned"
                        )

            session.allow_coop = room.allow_coop
            session.allow_abandon_worlds = room.allow_abandon_worlds
            session.save()


def add_member(session: MultiplayerSession, user: User) -> None:
    """Grants a user access to their team's session."""
    database.MultiplayerMembership.get_or_create(
        user=user,
        session=session,
        defaults={"admin": False},
    )


def remove_member(session: MultiplayerSession, user: User) -> None:
    """Revokes a user's access to their team's session, releasing any world they claimed."""
    with database.db.atomic():
        for association in database.WorldUserAssociation.find_all_for_user_in_session(user.id, session.id):
            association.delete_instance()

        database.MultiplayerMembership.delete().where(
            database.MultiplayerMembership.session == session,
            database.MultiplayerMembership.user == user,
        ).execute()


def get_world_for(session: MultiplayerSession, world_uuid: uuid.UUID) -> World:
    """Returns the world of the given session, refusing uuids belonging to any other session."""
    world = database.World.get_by_uuid(world_uuid)
    if world.session_id != session.id:
        raise error.WorldDoesNotExistError
    return world


def all_worlds_claimed(session: MultiplayerSession) -> bool:
    return all(list(world.associations) for world in session.get_ordered_worlds())
