from __future__ import annotations

import base64
import datetime
import json
import math
import typing
from collections.abc import Sequence

import fastapi
import peewee
import pydantic
from fastapi.params import Body
from peewee import Case
from starlette.websockets import WebSocket, WebSocketDisconnect

from randovania.game.game_enum import RandovaniaGame
from randovania.interface_common.worlds_configuration import WorldsConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.network_common import error
from randovania.network_common.async_race_room import (
    AsyncRaceEntryData,
    AsyncRaceRoomAdminData,
    AsyncRaceRoomEntry,
    AsyncRaceRoomListEntry,
    AsyncRaceRoomRaceStatus,
    AsyncRaceRoomUserStatus,
    AsyncRaceSettings,
    RaceRoomLeaderboard,
    RaceRoomLeaderboardEntry,
    race_uses_teams,
)
from randovania.network_common.async_race_room_endpoints import async_race_room_endpoints as endpoints
from randovania.network_common.audit import AuditEntry
from randovania.network_common.game_details import GameDetails
from randovania.network_common.multiplayer_session import (
    MAX_SESSION_NAME_LENGTH,
)
from randovania.network_common.signals import client_signals, server_signals
from randovania.server import database, lib
from randovania.server.async_race import team_session
from randovania.server.database import (
    AsyncRaceEntry,
    AsyncRaceEntryPause,
    AsyncRaceRoom,
    AsyncRaceTeam,
    AsyncRaceTimerHolder,
    BaseModel,
    User,
)
from randovania.server.server_app import RdvFastAPI, ServerApp, ServerAppDep, UserDep

if typing.TYPE_CHECKING:
    from randovania.network_common.user import RandovaniaUser

MAX_AUTH_TOKEN_LENGTH = 3600 * 24
MAX_TEAM_NAME_LENGTH = 50

router = fastapi.APIRouter(prefix=endpoints.prefix, tags=["async-race-room"])


def _get_async_race_socketio_room(room: AsyncRaceRoom, user: User) -> str:
    return f"async-race-{room.id}-{user.id}"


async def _verify_authorization(sa: ServerApp, user: User, room: AsyncRaceRoom, auth_token: str) -> None:
    """
    Checks for room password, current user membership and if the given auth token is valid.
    :param sa:
    :param user:
    :param room:
    :param auth_token:
    :return:
    """
    if room.password is not None:
        if database.AsyncRaceEntry.entry_for(room, user) is not None:
            return

        try:
            auth_data = sa.decrypt_and_b85_dict(auth_token)
            if auth_data["room_id"] != room.id:
                raise error.NotAuthorizedForActionError

            if datetime.datetime.now().timestamp() - auth_data["time"] > MAX_AUTH_TOKEN_LENGTH:
                raise error.NotAuthorizedForActionError

        except Exception:
            raise error.NotAuthorizedForActionError


def _fast_get_games_list_from_raw_layout(layout_description_json: bytes) -> list[RandovaniaGame]:
    """Gets a list of games in the given layout description, stored as bytes"""
    layout = LayoutDescription.bytes_to_dict(layout_description_json)
    # Skipping migration and decoding, to be fast

    present_games = set()
    for preset in layout["info"]["presets"]:
        present_games.add(preset["game"])

    return [g for g in RandovaniaGame.sorted_all_games() if g.value in present_games]


@router.get(endpoints.list_rooms_template)
async def list_rooms(sa: ServerAppDep, limit: int | None = None) -> Sequence[AsyncRaceRoomListEntry]:
    now = lib.datetime_now()

    def construct_helper(**args: typing.Any) -> AsyncRaceRoomListEntry:
        layout_description_json: bytes = args.pop("layout_description_json")
        games = None
        try:
            games = _fast_get_games_list_from_raw_layout(layout_description_json)
        except Exception:
            sa.logger.exception("Unable to get list of games from room")

        args["games"] = games
        args["creation_date"] = datetime.datetime.fromisoformat(args["creation_date"])
        args["start_date"] = datetime.datetime.fromisoformat(args["start_date"])
        args["end_date"] = datetime.datetime.fromisoformat(args["end_date"])
        args["has_password"] = bool(args["has_password"])
        args["race_status"] = AsyncRaceRoomRaceStatus.from_dates(args["start_date"], args["end_date"], now)
        return AsyncRaceRoomListEntry(**args)

    sessions = (
        AsyncRaceRoom.select(
            AsyncRaceRoom.id,
            AsyncRaceRoom.name,
            AsyncRaceRoom.layout_description_json,
            Case(None, ((AsyncRaceRoom.password.is_null(), False),), True).alias("has_password"),  # type: ignore[union-attr]
            AsyncRaceRoom.visibility,
            User.name.alias("creator"),  # type: ignore[attr-defined]
            AsyncRaceRoom.start_date.alias("start_date"),  # type: ignore[attr-defined]
            AsyncRaceRoom.end_date.alias("end_date"),  # type: ignore[attr-defined]
            AsyncRaceRoom.creation_date.alias("creation_date"),  # type: ignore[attr-defined]
        )
        .join(User, on=AsyncRaceRoom.creator)
        .group_by(AsyncRaceRoom.id)
        .order_by(AsyncRaceRoom.id.desc())  # type: ignore[attr-defined]
        .limit(limit)
        .objects(construct_helper)
    )

    return list(sessions)


def _verify_multiworld_compatible(layout: LayoutDescription, allow_coop: bool) -> None:
    """
    A room played in teams goes through a multiplayer session, so every preset in it must be
    one that multiworld supports. Which rooms need teams is decided by `race_uses_teams`.
    """
    if not race_uses_teams(layout.world_count, allow_coop):
        return

    for preset in layout.all_presets:
        if incompatible := preset.settings_incompatible_with_multiworld():
            raise error.InvalidActionError(
                f"Preset {preset.name} is not compatible with multiworld: {', '.join(incompatible)}"
            )


@router.post(endpoints.create_room_template)
async def create_room(
    sa: ServerAppDep,
    user: UserDep,
    layout_bin: typing.Annotated[pydantic.Base64Bytes, Body()],
    settings: AsyncRaceSettings,
) -> AsyncRaceRoomEntry:
    layout_decoded = bytes(layout_bin)
    try:
        layout = LayoutDescription.from_bytes(layout_decoded)
    except Exception as e:
        raise error.InvalidActionError(f"Unable to decode layout: {e}")

    if not (0 < len(settings.name) <= MAX_SESSION_NAME_LENGTH):
        raise error.InvalidActionError("Invalid session name length")

    _verify_multiworld_compatible(layout, settings.allow_coop)

    with database.db.atomic():
        new_room_id = AsyncRaceRoom.create(
            name=settings.name,
            password=settings.password,
            visibility=settings.visibility,
            # FIXME: That is a horrible name for something which takes the `bytes`
            layout_description_json=layout_decoded,
            game_details_json=json.dumps(GameDetails.from_layout(layout).as_json),
            creator=user,
            creation_date=lib.datetime_now(),
            start_date=settings.start_date.isoformat(),
            end_date=settings.end_date.isoformat(),
            allow_pause=settings.allow_pause,
            allow_coop=settings.allow_coop,
            allow_abandon_worlds=settings.allow_abandon_worlds,
            shared_team_timer=settings.shared_team_timer,
        ).id

    return await AsyncRaceRoom.get_by_id(new_room_id).create_session_entry(sa, user)


@router.patch(endpoints.change_room_template)
async def change_room_settings(
    sa: ServerAppDep,
    user: UserDep,
    room_id: int,
    settings: AsyncRaceSettings,
) -> AsyncRaceRoomEntry:
    """
    Updates the settings for the given room
    :param sa:
    :param user:
    :param room_id:
    :param settings_json:
    :return: A AsyncRaceRoomEntry, json encoded
    """
    room = AsyncRaceRoom.get_by_id(room_id)

    if room.creator != user:
        raise error.NotAuthorizedForActionError

    if not (0 < len(settings.name) <= MAX_SESSION_NAME_LENGTH):
        raise error.InvalidActionError("Invalid session name length")

    now = lib.datetime_now()
    old_status = AsyncRaceRoomRaceStatus.from_dates(room.start_datetime, room.end_datetime, now)
    new_status = AsyncRaceRoomRaceStatus.from_dates(settings.start_date, settings.end_date, now)

    status_order = [AsyncRaceRoomRaceStatus.SCHEDULED, AsyncRaceRoomRaceStatus.ACTIVE, AsyncRaceRoomRaceStatus.FINISHED]
    if status_order.index(new_status) < status_order.index(old_status):
        raise error.InvalidActionError("Can't go back in time for race status")

    layout = room.layout_description
    _verify_multiworld_compatible(layout, settings.allow_coop)

    has_entries = AsyncRaceEntry.select().where(AsyncRaceEntry.room == room).count() > 0
    if race_uses_teams(layout.world_count, settings.allow_coop) != room.uses_teams and has_entries:
        raise error.InvalidActionError("Can't change whether the race is played in teams after players have joined")

    if settings.shared_team_timer != room.shared_team_timer and has_entries:
        raise error.InvalidActionError("Can't change how the timer is kept after players have joined")

    room.name = settings.name
    room.start_datetime = settings.start_date
    room.end_datetime = settings.end_date
    room.visibility = settings.visibility
    room.allow_pause = settings.allow_pause
    room.allow_coop = settings.allow_coop
    room.allow_abandon_worlds = settings.allow_abandon_worlds
    room.shared_team_timer = settings.shared_team_timer

    with database.db.atomic():
        room.save()
        team_session.apply_room_settings(room)

    # TODO: Reusing the `room` after we set start_datetime/end_datetime breaks create_session_entry
    return await AsyncRaceRoom.get_by_id(room_id).create_session_entry(sa, user)


async def listen_to_room(sa: ServerApp, sid: str, room_id: int, listen: bool) -> None:
    room = AsyncRaceRoom.get_by_id(room_id)
    user = await sa.get_current_user(sid)
    socketio_room = _get_async_race_socketio_room(room, user)

    if listen:
        await sa.sio.enter_room(sid, socketio_room)
    else:
        await sa.sio.leave_room(sid, socketio_room)


@router.get(endpoints.get_room_template)
async def get_room(sa: ServerAppDep, user: UserDep, room_id: int, password: str | None = None) -> AsyncRaceRoomEntry:
    """
    Gets details about the given room id
    :param sa:
    :param user:
    :param room_id: The room to get details for
    :param password:
    :return: A AsyncRaceRoomEntry, json encoded
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    if room.password != password:
        raise error.WrongPasswordError
    return await room.create_session_entry(sa, user)


@router.get(endpoints.refresh_room_template)
async def refresh_room(sa: ServerAppDep, user: UserDep, room_id: int, auth_token: str) -> AsyncRaceRoomEntry:
    """
    Gets details about the given room id
    :param sa:
    :param user:
    :param room_id: The room to get details for
    :param auth_token:
    :return: A AsyncRaceRoomEntry, json encoded
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    await _verify_authorization(sa, user, room, auth_token)
    return await room.create_session_entry(sa, user)


@router.get(endpoints.room_leaderboard_template)
async def get_leaderboard(
    sa: ServerAppDep,
    user: UserDep,
    room_id: int,
    auth_token: str,
) -> RaceRoomLeaderboard:
    """
    Gets the race results. Only accessible after the end time is reached.
    :param sa:
    :param user:
    :param room_id: The room to get details for
    :param auth_token:
    :return: A RaceRoomLeaderboard, json encoded
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    await _verify_authorization(sa, user, room, auth_token)

    if room.end_datetime > lib.datetime_now():
        raise error.NotAuthorizedForActionError

    def leaderboard_entry_for(
        holder: AsyncRaceTimerHolder,
        display_name: str,
        members: list[RandovaniaUser],
    ) -> RaceRoomLeaderboardEntry | None:
        match holder.timer_status():
            case AsyncRaceRoomUserStatus.FINISHED:
                time = holder.elapsed_time()
                assert time is not None
            case AsyncRaceRoomUserStatus.FORFEITED | AsyncRaceRoomUserStatus.STARTED:
                time = None
            case _:
                return None

        return RaceRoomLeaderboardEntry(display_name=display_name, time=time, members=members)

    entries = []
    if room.uses_teams:
        for team in AsyncRaceTeam.select().where(AsyncRaceTeam.room == room):
            members = [member.user.as_randovania_user() for member in team.all_members()]
            if (result := leaderboard_entry_for(team, team.name, members)) is not None:
                entries.append(result)
    else:
        for entry in room.entries:
            entry_user = entry.user.as_randovania_user()
            if (result := leaderboard_entry_for(entry, entry_user.name, [entry_user])) is not None:
                entries.append(result)

    entries.sort(key=lambda key: key.time.total_seconds() if key.time is not None else math.inf)

    return RaceRoomLeaderboard(entries=entries, uses_teams=room.uses_teams)


@router.get(endpoints.room_layout_template, response_class=fastapi.Response)
async def get_layout(sa: ServerAppDep, user: UserDep, room_id: int, auth_token: str) -> fastapi.Response:
    """
    Gets the layout description for the room, if it has finished
    :param sa:
    :param user:
    :param room_id: The room to get details for
    :param auth_token:
    :return: A LayoutDescription, byte-encoded
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    await _verify_authorization(sa, user, room, auth_token)

    if room.end_datetime > lib.datetime_now():
        raise error.NotAuthorizedForActionError

    return fastapi.Response(content=room.layout_description_json, media_type="application/octet-stream")


@router.get(endpoints.room_audit_log_template)
async def get_audit_log(
    sa: ServerAppDep,
    user: UserDep,
    room_id: int,
    auth_token: str,
) -> Sequence[AuditEntry]:
    """
    Gets the audit log for the given room.
    :param sa:
    :param user:
    :param room_id: The room to get audit log for
    :param auth_token:
    :return: A list of json-encoded AuditEntry
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    await _verify_authorization(sa, user, room, auth_token)

    if room.creator != user:
        raise error.NotAuthorizedForActionError

    return [log.as_entry() for log in room.audit_log]


@router.get(endpoints.room_admin_data_template)
async def admin_get_admin_data(user: UserDep, room_id: int) -> AsyncRaceRoomAdminData:
    """
    Gets the all details of every user who has joined the room. Only accessible by admins.
    :param sa:
    :param user:
    :param room_id: The room to get details for
    :return: A AsyncRaceRoomAdminData, json encoded
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    if room.creator != user:
        raise error.NotAuthorizedForActionError

    if room.uses_teams:
        participants = [team.create_admin_entry() for team in AsyncRaceTeam.select().where(AsyncRaceTeam.room == room)]
    else:
        participants = [entry.create_admin_entry() for entry in room.entries]

    return AsyncRaceRoomAdminData(users=participants)


@router.post(endpoints.room_admin_entries_template)
async def admin_update_entries(
    sa: ServerAppDep, user: UserDep, room_id: int, new_entries: list[AsyncRaceEntryData]
) -> AsyncRaceRoomEntry:
    """
    Updates multiple entries for the given room, all at once.
    :param sa:
    :param user:
    :param room_id:
    :param raw_new_entries: The list of entries to modify.
    :return: A AsyncRaceRoomEntry, json encoded
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    if room.creator != user:
        raise error.NotAuthorizedForActionError

    max_date_start = datetime.datetime(datetime.MAXYEAR, 1, 1, tzinfo=datetime.UTC)
    max_date_finish = datetime.datetime(datetime.MAXYEAR, 1, 2, tzinfo=datetime.UTC)

    with database.db.atomic():
        for modification in new_entries:
            if not (
                modification.join_date
                < (modification.start_date or max_date_start)
                < (modification.finish_date or max_date_finish)
            ):
                raise error.InvalidActionError(f"Invalid dates for {modification.display_name}")

            holder: AsyncRaceTimerHolder | None
            if modification.team_id is not None:
                holder = AsyncRaceTeam.get_or_none(AsyncRaceTeam.id == modification.team_id, room=room)
            elif modification.user is not None:
                holder = database.AsyncRaceEntry.entry_for(room, modification.user.id)
            else:
                holder = None

            if holder is None:
                raise error.InvalidActionError(f"{modification.display_name} is not a member of this room")

            holder.start_datetime = modification.start_date
            holder.finish_datetime = modification.finish_date
            holder.forfeit = modification.forfeit
            holder.submission_notes = modification.submission_notes
            holder.proof_url = modification.proof_url
            holder.save()

        database.AsyncRaceAuditEntry.create(
            room=room,
            user=user,
            message=f"Modified entries for {[', '.join(mod.display_name for mod in new_entries)]}.",
        )

    return await AsyncRaceRoom.get_by_id(room_id).create_session_entry(sa, user)


@router.post(endpoints.room_join_and_export_template)
async def join_and_export(
    sa: ServerAppDep,
    user: UserDep,
    room_id: int,
    auth_token: str,
    cosmetic_json: typing.Annotated[dict, Body()],
) -> dict:
    """

    :param sa:
    :param user:
    :param room_id: The room to join
    :param auth_token:
    :param cosmetic_json: The json for a BaseCosmeticPatches subclass. Which subclass depends on the room's game,
    so it can only be decoded after the room is known.
    :return:
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    await _verify_authorization(sa, user, room, auth_token)

    if room.uses_teams:
        raise error.InvalidActionError("This room is played in teams; join a team first")

    if room.get_race_status(lib.datetime_now()) != AsyncRaceRoomRaceStatus.ACTIVE:
        raise error.NotAuthorizedForActionError("Room is not active")

    layout_description = room.layout_description
    worlds_config = WorldsConfiguration(
        world_index=0,
        world_names={0: "World"},
        uuids={},
        session_name=None,
        is_coop=False,
    )
    preset = layout_description.get_preset(worlds_config.world_index)

    try:
        cosmetic_patches = preset.game.data.layout.cosmetic_patches.from_json(cosmetic_json)
    except Exception as e:
        raise error.InvalidActionError(f"Invalid cosmetic patches for {preset.game.long_name}: {e}")

    entry, _ = database.AsyncRaceEntry.get_or_create(
        room=room,
        user=user,
    )
    if not entry.has_exported:
        entry.has_exported = True
        entry.save()

    data_factory = preset.game.patch_data_factory(layout_description, worlds_config, cosmetic_patches)
    rdv_meta = data_factory.create_default_patcher_data_meta()
    rdv_meta["in_race_setting"] = True
    try:
        result = data_factory.create_data(rdv_meta)
        return result
    except Exception as e:
        raise error.InvalidActionError(f"Unable to export game: {e}")


def _get_own_team(room: AsyncRaceRoom, user: User) -> AsyncRaceTeam:
    """The team the given user belongs to."""
    entry = database.AsyncRaceEntry.entry_for(room, user)
    if entry is None or entry.team is None:
        raise error.NotAuthorizedForActionError("You are not part of a team in this room")
    return entry.team


def _require_teams(room: AsyncRaceRoom) -> None:
    if not room.uses_teams:
        raise error.InvalidActionError("This room is not played in teams")


@router.post(endpoints.room_teams_template)
async def create_team(
    sa: ServerAppDep,
    user: UserDep,
    room_id: int,
    auth_token: str,
    team_name: str,
) -> AsyncRaceRoomEntry:
    """
    Creates a new team in a room played in teams, with the current user as its first member and
    captain, along with the hidden session that hosts the team's multiworld.
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    await _verify_authorization(sa, user, room, auth_token)
    _require_teams(room)

    if not (0 < len(team_name) <= MAX_TEAM_NAME_LENGTH):
        raise error.InvalidActionError("Invalid team name length")

    if room.get_race_status(lib.datetime_now()) == AsyncRaceRoomRaceStatus.FINISHED:
        raise error.NotAuthorizedForActionError("Room has already finished")

    if database.AsyncRaceEntry.entry_for(room, user) is not None:
        raise error.InvalidActionError("You are already part of a team in this room")

    with database.db.atomic():
        team = AsyncRaceTeam.create(
            room=room, name=team_name, captain=user, join_code=AsyncRaceTeam.new_join_code(room)
        )
        session = team_session.create_session_for_team(room, team)
        team_session.add_member(session, user)
        database.AsyncRaceEntry.create(room=room, user=user, team=team)
        database.AsyncRaceAuditEntry.create(room=room, user=user, message=f"Created team {team_name}.")

    return await AsyncRaceRoom.get_by_id(room_id).create_session_entry(sa, user)


@router.get(endpoints.room_team_join_code_template)
async def get_team_join_code(user: UserDep, room_id: int) -> str:
    """
    Returns the code that lets someone else join the current user's team.
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    team = _get_own_team(room, user)

    return team.join_code


@router.post(endpoints.room_join_team_template)
async def join_team(sa: ServerAppDep, user: UserDep, room_id: int, join_code: str) -> AsyncRaceRoomEntry:
    """
    Joins an existing team using a code obtained from one of its members.
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    _require_teams(room)

    if room.get_race_status(lib.datetime_now()) == AsyncRaceRoomRaceStatus.FINISHED:
        raise error.NotAuthorizedForActionError("Room has already finished")

    team = AsyncRaceTeam.get_or_none(AsyncRaceTeam.room == room, AsyncRaceTeam.join_code == join_code)
    if team is None:
        raise error.InvalidActionError("Invalid join code")

    if database.AsyncRaceEntry.entry_for(room, user) is not None:
        raise error.InvalidActionError("You are already part of a team in this room")

    if team.timer_status() != AsyncRaceRoomUserStatus.JOINED:
        raise error.InvalidActionError("This team has already started")

    session = team.session
    if session is None:
        raise error.ServerError

    with database.db.atomic():
        team_session.add_member(session, user)
        database.AsyncRaceEntry.create(room=room, user=user, team=team)
        database.AsyncRaceAuditEntry.create(room=room, user=user, message=f"Joined team {team.name}.")

    return await AsyncRaceRoom.get_by_id(room_id).create_session_entry(sa, user)


@router.post(endpoints.room_leave_team_template)
async def leave_team(sa: ServerAppDep, user: UserDep, room_id: int) -> AsyncRaceRoomEntry:
    """
    Leaves the current user's team. Refused once they have exported a world, since by then
    they have seen part of a seed that every other team in the room also plays.
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    _require_teams(room)

    entry = database.AsyncRaceEntry.entry_for(room, user)
    if entry is None or entry.team is None:
        raise error.InvalidActionError("You are not part of a team in this room")

    team = entry.team
    if entry.has_exported:
        raise error.InvalidActionError("Can't leave a team after exporting a game")

    if team.timer_status() != AsyncRaceRoomUserStatus.JOINED:
        raise error.InvalidActionError("Can't leave a team that has already started")

    with database.db.atomic():
        session = team.session
        if session is not None:
            team_session.remove_member(session, user)
        entry.delete_instance()
        database.AsyncRaceAuditEntry.create(room=room, user=user, message=f"Left team {team.name}.")

        remaining = team.all_members()
        if not remaining:
            team.delete_with_session()
        elif team.is_captain(user):
            team.promote_new_captain()
            database.AsyncRaceAuditEntry.create(
                room=room,
                user=user,
                message=f"{remaining[0].user.name} is now the captain of team {team.name}.",
            )

    return await AsyncRaceRoom.get_by_id(room_id).create_session_entry(sa, user)


def _check_team_can_start(team: AsyncRaceTeam) -> None:
    """
    A team may start once it is actually able to play: every world of its multiworld has someone
    on it, and nobody on the team is left without a world.
    """
    session = team.session
    if session is None:
        raise error.ServerError

    if not team_session.all_worlds_claimed(session):
        raise error.InvalidActionError("Every world must be claimed before starting")

    missing = team.members_without_world()
    if missing:
        names = ", ".join(member.user.name for member in missing)
        raise error.InvalidActionError(f"Every member must claim a world before starting: {names}")


def _authorized_timer_holder_for(
    room: AsyncRaceRoom,
    entry: AsyncRaceEntry,
    user: User,
    new_state: AsyncRaceRoomUserStatus,
) -> AsyncRaceTimerHolder:
    """
    Decides whose timer a requested state change drives, and raises if the user isn't allowed to
    drive it.
    """
    team = entry.team
    if team is None:
        return entry

    if room.shared_team_timer:
        if not team.is_captain(user):
            raise error.NotAuthorizedForActionError("Only the team's captain can control the timer")
        return team

    # The race is started for a team exactly while the team itself carries a start date, whatever
    # its members have done since.
    starts_the_race = (
        new_state == AsyncRaceRoomUserStatus.STARTED and team.start_date is None
    ) or new_state == AsyncRaceRoomUserStatus.JOINED

    # Forfeiting, and taking a forfeit back, belong to the whole team as well.
    forfeits = new_state == AsyncRaceRoomUserStatus.FORFEITED or team.forfeit

    if starts_the_race or forfeits:
        if not team.is_captain(user):
            raise error.NotAuthorizedForActionError(
                "Only the team's captain can forfeit the race for the team"
                if forfeits
                else "Only the team's captain can start the race"
            )
        return team

    return entry


def _cascade_start_to_members(team: AsyncRaceTeam, start: datetime.datetime | None) -> list[BaseModel]:
    """
    Applies the captain starting (or un-starting) the race to every member's own timer, for rooms
    that accumulate each member's time instead of sharing a single one.
    """
    members = team.all_members()
    if start is None:
        # Undoing the start resets whatever the members did after it.
        AsyncRaceEntryPause.delete().where(
            AsyncRaceEntryPause.entry.in_([member.id for member in members])  # type: ignore[union-attr]
        ).execute()

    for member in members:
        member.start_datetime = start
        if start is None:
            member.finish_datetime = None
            member.paused = False
            member.forfeit = False

    return list(members)


async def perform_state_change(
    room: AsyncRaceRoom,
    user: User,
    new_state: AsyncRaceRoomUserStatus,
) -> None:
    entry = database.AsyncRaceEntry.entry_for(room, user)
    if entry is None:
        raise error.NotAuthorizedForActionError

    holder = _authorized_timer_holder_for(room, entry, user, new_state)
    team = entry.team
    # Whether this change belongs to the team as a whole rather than to this one member.
    drives_whole_team = isinstance(holder, AsyncRaceTeam)
    accumulates = team is not None and not room.shared_team_timer

    if drives_whole_team:
        # Deliberately the base implementation, not AsyncRaceTeam's override: the transitions below
        # act on the team's own columns, while the override derives an accumulating team's status
        # from its members instead.
        old_state = AsyncRaceTimerHolder.timer_status(holder)
    else:
        old_state = holder.timer_status()

    now = lib.datetime_now()

    # Ignore transitions for doing nothing
    # These can happen if the client doesn't get updated and the user retries what they did last.
    if old_state == new_state:
        return

    things_to_save: list[AsyncRaceTimerHolder | BaseModel] = [holder]

    match (old_state, new_state):
        case (AsyncRaceRoomUserStatus.JOINED, AsyncRaceRoomUserStatus.STARTED):
            if team is not None:
                _check_team_can_start(team)
            holder.start_datetime = now
            if accumulates and drives_whole_team:
                assert team is not None
                things_to_save.extend(_cascade_start_to_members(team, now))
            # FIXME: limit distance of start date from join date

        case (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.JOINED):
            # Undoing pressing "Start"
            holder.start_datetime = None
            if accumulates and drives_whole_team:
                assert team is not None
                things_to_save.extend(_cascade_start_to_members(team, None))

        case (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.PAUSED):
            # Pressing Pause
            if not room.allow_pause:
                raise error.InvalidActionError("Pausing not allowed")

            AsyncRaceEntryPause.create_for(holder, now)
            holder.paused = True

        case (AsyncRaceRoomUserStatus.PAUSED, AsyncRaceRoomUserStatus.STARTED):
            # Undoing pressing "Pause"
            pause = AsyncRaceEntryPause.active_pause(holder)
            assert pause is not None
            pause.end = now
            things_to_save.append(pause)
            holder.paused = False

        case (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.FINISHED):
            # Pressing Finish
            holder.finish_datetime = now

        case (AsyncRaceRoomUserStatus.FINISHED, AsyncRaceRoomUserStatus.STARTED):
            # Undoing pressing "Finish"
            holder.finish_datetime = None

        case (AsyncRaceRoomUserStatus.STARTED | AsyncRaceRoomUserStatus.FINISHED, AsyncRaceRoomUserStatus.FORFEITED):
            # Pressing Forfeit
            holder.forfeit = True

        case (AsyncRaceRoomUserStatus.FORFEITED, AsyncRaceRoomUserStatus.STARTED | AsyncRaceRoomUserStatus.FINISHED):
            # Undoing pressing Forfeit
            holder.forfeit = False

        case (_, _):
            raise error.InvalidActionError("Unsupported state transition")

    if team is None:
        subject = ""
    elif drives_whole_team:
        subject = f" of team {team.name}"
    else:
        subject = f" of themselves in team {team.name}"

    with database.db.atomic():
        database.AsyncRaceAuditEntry.create(
            room=room,
            user=user,
            message=f"Changed state{subject} from {old_state.value} to {new_state.value}",
        )
        for it in things_to_save:
            it.save()


@router.post(endpoints.room_state_template)
async def change_state(
    sa: ServerAppDep, user: UserDep, room_id: int, new_state: AsyncRaceRoomUserStatus
) -> AsyncRaceRoomEntry:
    """
    Adjusts the start date, finish date or forfeit flag of the user's entry based on the requested state.
    :param sa:
    :param user:
    :param room_id:
    :param new_state:
    :return:
    """
    room = AsyncRaceRoom.get_by_id(room_id)

    await perform_state_change(room, user, new_state)

    return await room.create_session_entry(sa, user)


@router.get(endpoints.room_own_proof_template)
async def get_own_proof(user: UserDep, room_id: int) -> tuple[str, str]:
    """
    This endpoint allows a user to request their own submission notes and proof url.
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    entry = database.AsyncRaceEntry.entry_for(room, user)
    if entry is None:
        raise error.NotAuthorizedForActionError

    holder = entry.timer_holder()
    if holder.timer_status() != AsyncRaceRoomUserStatus.FINISHED:
        raise error.InvalidActionError("Only possible to submit proof after finishing")

    database.AsyncRaceAuditEntry.create(room=room, user=user, message="Requested own submission notes and proof.")

    return holder.submission_notes, holder.proof_url


@router.post(endpoints.room_submit_proof_template)
async def submit_proof(user: UserDep, room_id: int, submission_notes: str, proof_url: str) -> None:
    """
    This endpoint allows a user to record submission notes and a link to proof for their run.
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    entry = database.AsyncRaceEntry.entry_for(room, user)
    if entry is None:
        raise error.NotAuthorizedForActionError

    holder = entry.timer_holder()
    if holder.timer_status() != AsyncRaceRoomUserStatus.FINISHED:
        raise error.InvalidActionError("Only possible to submit proof after finishing")

    database.AsyncRaceAuditEntry.create(room=room, user=user, message="Updated submission notes and proof.")

    holder.submission_notes = submission_notes
    holder.proof_url = proof_url
    holder.save()


@router.get(endpoints.room_livesplit_url_template)
async def get_livesplit_url(sa: ServerAppDep, user: UserDep, room_id: int) -> str:
    room = AsyncRaceRoom.get_by_id(room_id)
    entry = database.AsyncRaceEntry.entry_for(room, user)
    if entry is None:
        raise error.NotAuthorizedForActionError

    if entry.team is not None and room.shared_team_timer and not entry.team.is_captain(user):
        raise error.NotAuthorizedForActionError("Only the team's captain can control the timer")

    token = base64.urlsafe_b64encode(sa.encrypt_str(f"{user.id}/{room_id}")).decode("ascii")

    return str(
        sa.app.url_path_for("livesplit_integration", room_id=room_id, token=token).make_absolute_url(
            sa.configuration["server_address"]
        )
    )


_livesplit_event_mapping = {
    "Reset": AsyncRaceRoomUserStatus.JOINED,
    "Started": AsyncRaceRoomUserStatus.STARTED,
    "Paused": AsyncRaceRoomUserStatus.PAUSED,
    "Resumed": AsyncRaceRoomUserStatus.STARTED,
    "Finished": AsyncRaceRoomUserStatus.FINISHED,
}


async def emit_async_room_update(sa: ServerApp, room: AsyncRaceRoom, sid_or_user: str | User) -> None:
    changed_by = await sa.get_current_user(sid_or_user) if isinstance(sid_or_user, str) else sid_or_user

    users = [changed_by]
    entry = database.AsyncRaceEntry.entry_for(room, changed_by)
    if entry is not None and entry.team is not None:
        users = [member.user for member in entry.team.all_members()]

    for user in users:
        await client_signals.AsyncRaceRoomUpdate.emit(
            sa,
            to=_get_async_race_socketio_room(room, user),
            namespace="/",
        )((await room.create_session_entry(sa, user)).as_json)


@router.websocket(endpoints.room_livesplit_integration_template)
async def livesplit_integration(
    websocket: WebSocket,
    room_id: int,
    token: str,
) -> None:
    app: RdvFastAPI = websocket.app

    # Extract the user id and room_id from an encrypted value.
    # The only way to get a valid token is to call `get_livesplit_url`, which checks if the user is an
    # active member of the race, solving the lack of authentication needed in this endpoint.
    user_id_str, room_id_confirm = app.sa.decrypt_str(base64.urlsafe_b64decode(token)).split("/")
    user_id = int(user_id_str)

    if room_id != int(room_id_confirm):
        await websocket.close(reason="Invalid url")
        return

    try:
        room = AsyncRaceRoom.get_by_id(room_id)
        user = User.get_by_id(user_id)

    except peewee.DoesNotExist:
        await websocket.close(reason="Invalid url")
        return

    entry = database.AsyncRaceEntry.entry_for(room, user)
    if entry is None:
        await websocket.close(reason="Not a member")
        return

    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
        except WebSocketDisconnect:
            return

        # The LiveSplit One API is documented in their source code:
        # https://github.com/LiveSplit/livesplit-core/blob/master/src/networking/server_protocol.rs
        #
        # While the messages sent from them to us are handled in this handleEvent function:
        # https://github.com/LiveSplit/LiveSplitOne/blob/master/src/ui/LiveSplit.tsx#L904
        # And events defined here: https://github.com/LiveSplit/livesplit-core/blob/master/src/event.rs

        try:
            event: dict = json.loads(data)
        except json.JSONDecodeError as e:
            app.sa.logger.info("Received invalid json from livesplit: %s %s", str(e), data)
            continue

        new_state = _livesplit_event_mapping.get(event.get("event"))  # type: ignore[arg-type]
        if new_state is not None:
            if new_state is AsyncRaceRoomUserStatus.PAUSED and not room.allow_pause:
                await websocket.send_json({"command": "undoAllPauses"})
                continue

            try:
                await perform_state_change(room, user, new_state)
                await emit_async_room_update(app.sa, room, user)
            except error.BaseNetworkError as e:
                app.sa.logger.info("Invalid transition to %s received from livesplit: %s", str(new_state), str(e))


def setup_app(sa: ServerApp) -> None:
    sa.app.include_router(router)
    server_signals.AsyncRace.ListenToRoom.register(sa, listen_to_room, with_header_check=True)
