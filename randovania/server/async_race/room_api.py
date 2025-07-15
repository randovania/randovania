import datetime
import json
import math
import typing

from peewee import Case
from retro_data_structures.json_util import JsonArray

from randovania.game.game_enum import RandovaniaGame
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib.json_lib import JsonObject, JsonType
from randovania.network_common import error
from randovania.network_common.async_race_room import (
    AsyncRaceEntryData,
    AsyncRaceRoomAdminData,
    AsyncRaceRoomListEntry,
    AsyncRaceRoomRaceStatus,
    AsyncRaceRoomUserStatus,
    AsyncRaceSettings,
    RaceRoomLeaderboard,
    RaceRoomLeaderboardEntry,
)
from randovania.network_common.game_details import GameDetails
from randovania.network_common.multiplayer_session import (
    MAX_SESSION_NAME_LENGTH,
)
from randovania.server import database, lib
from randovania.server.database import (
    AsyncRaceEntryPause,
    AsyncRaceRoom,
    User,
)
from randovania.server.server_app import ServerApp

MAX_AUTH_TOKEN_LENGTH = 3600 * 24


def _verify_authorization(sa: ServerApp, room: AsyncRaceRoom, auth_token: str) -> None:
    """
    Checks for room password, current user membership and if the given auth token is valid.
    :param sa:
    :param room:
    :param auth_token:
    :return:
    """
    if room.password is not None:
        if database.AsyncRaceEntry.entry_for(room, sa.get_current_user()) is not None:
            return

        try:
            auth_data = sa.decrypt_dict(auth_token)
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


def list_rooms(sa: ServerApp, limit: int | None) -> JsonType:
    now = lib.datetime_now()

    def construct_helper(**args: typing.Any) -> AsyncRaceRoomListEntry:
        layout_description_json: bytes = args.pop("layout_description_json")
        games = None
        try:
            games = _fast_get_games_list_from_raw_layout(layout_description_json)
        except Exception:
            lib.logger().exception("Unable to get list of games from room")

        args["games"] = games
        args["creation_date"] = datetime.datetime.fromisoformat(args["creation_date"])
        args["start_date"] = datetime.datetime.fromisoformat(args["start_date"])
        args["end_date"] = datetime.datetime.fromisoformat(args["end_date"])
        args["has_password"] = bool(args["has_password"])
        args["race_status"] = AsyncRaceRoomRaceStatus.from_dates(args["start_date"], args["end_date"], now)
        return AsyncRaceRoomListEntry(**args)

    sessions: list[AsyncRaceRoomListEntry] = (
        AsyncRaceRoom.select(
            AsyncRaceRoom.id,
            AsyncRaceRoom.name,
            AsyncRaceRoom.layout_description_json,
            Case(None, ((AsyncRaceRoom.password.is_null(), False),), True).alias("has_password"),
            AsyncRaceRoom.visibility,
            User.name.alias("creator"),
            AsyncRaceRoom.start_date.alias("start_date"),
            AsyncRaceRoom.end_date.alias("end_date"),
            AsyncRaceRoom.creation_date.alias("creation_date"),
        )
        .join(User, on=AsyncRaceRoom.creator)
        .group_by(AsyncRaceRoom.id)
        .order_by(AsyncRaceRoom.id.desc())
        .limit(limit)
        .objects(construct_helper)
    )

    return [session.as_json for session in sessions]


def create_room(sa: ServerApp, layout_bin: bytes, settings_json: JsonObject) -> JsonObject:
    current_user = sa.get_current_user()

    layout = LayoutDescription.from_bytes(layout_bin)
    settings = AsyncRaceSettings.from_json(settings_json)

    if not (0 < len(settings.name) <= MAX_SESSION_NAME_LENGTH):
        raise error.InvalidActionError("Invalid session name length")

    if layout.world_count != 1:
        raise error.InvalidActionError("Only single world games allowed")

    with database.db.atomic():
        new_room_id = AsyncRaceRoom.create(
            name=settings.name,
            password=settings.password,
            visibility=settings.visibility,
            layout_description_json=layout_bin,
            game_details_json=json.dumps(GameDetails.from_layout(layout).as_json),
            creator=current_user,
            creation_date=lib.datetime_now(),
            start_date=settings.start_date,
            end_date=settings.end_date,
            allow_pause=settings.allow_pause,
        ).id

    return AsyncRaceRoom.get_by_id(new_room_id).create_session_entry(sa).as_json


def change_room_settings(sa: ServerApp, room_id: int, settings_json: JsonObject) -> JsonObject:
    """
    Updates the settings for the given room
    :param sa:
    :param room_id:
    :param settings_json:
    :return: A AsyncRaceRoomEntry, json encoded
    """
    current_user = sa.get_current_user()
    settings = AsyncRaceSettings.from_json(settings_json)

    room = AsyncRaceRoom.get_by_id(room_id)

    if room.creator != current_user:
        raise error.NotAuthorizedForActionError

    if not (0 < len(settings.name) <= MAX_SESSION_NAME_LENGTH):
        raise error.InvalidActionError("Invalid session name length")

    now = lib.datetime_now()
    old_status = AsyncRaceRoomRaceStatus.from_dates(room.start_datetime, room.end_datetime, now)
    new_status = AsyncRaceRoomRaceStatus.from_dates(settings.start_date, settings.end_date, now)

    status_order = [AsyncRaceRoomRaceStatus.SCHEDULED, AsyncRaceRoomRaceStatus.ACTIVE, AsyncRaceRoomRaceStatus.FINISHED]
    if status_order.index(new_status) < status_order.index(old_status):
        raise error.InvalidActionError("Can't go back in time for race status")

    room.name = settings.name
    room.start_datetime = settings.start_date
    room.end_datetime = settings.end_date
    room.visibility = settings.visibility
    room.allow_pause = settings.allow_pause
    room.save()

    # TODO: Reusing the `room` after we set start_datetime/end_datetime breaks create_session_entry
    return AsyncRaceRoom.get_by_id(room_id).create_session_entry(sa).as_json


def get_room(sa: ServerApp, room_id: int, password: str | None) -> JsonType:
    """
    Gets details about the given room id
    :param sa:
    :param room_id: The room to get details for
    :param password:
    :return: A AsyncRaceRoomEntry, json encoded
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    if room.password != password:
        raise error.WrongPasswordError
    return room.create_session_entry(sa).as_json


def refresh_room(sa: ServerApp, room_id: int, auth_token: str) -> JsonType:
    """
    Gets details about the given room id
    :param sa:
    :param room_id: The room to get details for
    :param auth_token:
    :return: A AsyncRaceRoomEntry, json encoded
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    _verify_authorization(sa, room, auth_token)
    return room.create_session_entry(sa).as_json


def get_leaderboard(sa: ServerApp, room_id: int, auth_token: str) -> JsonType:
    """
    Gets the race results. Only accessible after the end time is reached.
    :param sa:
    :param room_id: The room to get details for
    :param auth_token:
    :return: A RaceRoomLeaderboard, json encoded
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    _verify_authorization(sa, room, auth_token)

    if room.end_datetime > lib.datetime_now():
        raise error.NotAuthorizedForActionError

    entries = []
    for entry in room.entries:
        match entry.user_status():
            case AsyncRaceRoomUserStatus.FINISHED:
                entries.append(
                    RaceRoomLeaderboardEntry(
                        user=entry.user.as_randovania_user(),
                        time=entry.finish_datetime
                        - entry.start_datetime
                        - sum((pause.length for pause in entry.pauses), datetime.timedelta(seconds=0)),
                    )
                )
            case AsyncRaceRoomUserStatus.FORFEITED | AsyncRaceRoomUserStatus.STARTED:
                entries.append(
                    RaceRoomLeaderboardEntry(
                        user=entry.user.as_randovania_user(),
                        time=None,
                    )
                )

    entries.sort(key=lambda key: key.time.total_seconds() if key.time is not None else math.inf)

    return RaceRoomLeaderboard(entries).as_json


def get_layout(sa: ServerApp, room_id: int, auth_token: str) -> bytes:
    """
    Gets the layout description for the room, if it has finished
    :param sa:
    :param room_id: The room to get details for
    :param auth_token:
    :return: A LayoutDescription, byte-encoded
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    _verify_authorization(sa, room, auth_token)

    if room.end_datetime > lib.datetime_now():
        raise error.NotAuthorizedForActionError

    return room.layout_description_json


def get_audit_log(sa: ServerApp, room_id: int, auth_token: str) -> JsonArray:
    """
    Gets the audit log for the given room.
    :param sa:
    :param room_id: The room to get audit log for
    :param auth_token:
    :return: A list of json-encoded AuditEntry
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    _verify_authorization(sa, room, auth_token)

    return [log.as_entry().as_json for log in room.audit_log]


def admin_get_admin_data(sa: ServerApp, room_id: int) -> JsonType:
    """
    Gets the all details of every user who has joined the room. Only accessible by admins.
    :param sa:
    :param room_id: The room to get details for
    :return: A AsyncRaceRoomAdminData, json encoded
    """
    user = sa.get_current_user()
    room = AsyncRaceRoom.get_by_id(room_id)
    if room.creator != user:
        raise error.NotAuthorizedForActionError

    return AsyncRaceRoomAdminData(
        users=[entry.create_admin_entry() for entry in room.entries],
    ).as_json


def admin_update_entries(sa: ServerApp, room_id: int, raw_new_entries: JsonType) -> JsonType:
    """
    Updates multiple entries for the given room, all at once.
    :param sa:
    :param room_id:
    :param raw_new_entries: The list of entries to modify.
    :return: A AsyncRaceRoomEntry, json encoded
    """
    user = sa.get_current_user()
    room = AsyncRaceRoom.get_by_id(room_id)
    if room.creator != user:
        raise error.NotAuthorizedForActionError

    new_entries = [AsyncRaceEntryData.from_json(e) for e in raw_new_entries]
    max_date_start = datetime.datetime(datetime.MAXYEAR, 1, 1, tzinfo=datetime.UTC)
    max_date_finish = datetime.datetime(datetime.MAXYEAR, 1, 2, tzinfo=datetime.UTC)

    with database.db.atomic():
        for modification in new_entries:
            if not (
                modification.join_date
                < (modification.start_date or max_date_start)
                < (modification.finish_date or max_date_finish)
            ):
                raise error.InvalidActionError(f"Invalid dates for {modification.user.name}")

            entry = database.AsyncRaceEntry.entry_for(room, modification.user.id)
            entry.start_datetime = modification.start_date
            entry.finish_datetime = modification.finish_date
            entry.forfeit = modification.forfeit
            entry.submission_notes = modification.submission_notes
            entry.proof_url = modification.proof_url
            entry.save()

        database.AsyncRaceAuditEntry.create(
            room=room,
            user=sa.get_current_user(),
            message=f"Modified entries for {[', '.join(mod.user.name for mod in new_entries)]}.",
        )

    return AsyncRaceRoom.get_by_id(room_id).create_session_entry(sa).as_json


def join_and_export(sa: ServerApp, room_id: int, auth_token: str, cosmetic_json: JsonType) -> JsonType:
    """

    :param sa:
    :param room_id: The room to join
    :param auth_token:
    :param cosmetic_json:
    :return:
    """
    user = sa.get_current_user()
    room = AsyncRaceRoom.get_by_id(room_id)
    _verify_authorization(sa, room, auth_token)

    if room.get_race_status(lib.datetime_now()) != AsyncRaceRoomRaceStatus.ACTIVE:
        raise error.NotAuthorizedForActionError("Room is not active")

    database.AsyncRaceEntry.get_or_create(
        room=room,
        user=user,
    )

    layout_description = room.layout_description
    players_config = PlayersConfiguration(
        player_index=0,
        player_names={0: "World"},
        uuids={},
        session_name=None,
        is_coop=False,
    )
    preset = layout_description.get_preset(players_config.player_index)
    cosmetic_patches = preset.game.data.layout.cosmetic_patches.from_json(cosmetic_json)

    data_factory = preset.game.patch_data_factory(layout_description, players_config, cosmetic_patches)
    rdv_meta = data_factory.create_default_patcher_data_meta()
    rdv_meta["in_race_setting"] = True
    try:
        result = data_factory.create_data(rdv_meta)
        return result
    except Exception as e:
        raise error.InvalidActionError(f"Unable to export game: {e}")


def change_state(sa: ServerApp, room_id: int, new_state: str) -> JsonType:
    """
    Adjusts the start date, finish date or forfeit flag of the user's entry based on the requested state.
    :param sa:
    :param room_id:
    :param new_state:
    :return:
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    user = sa.get_current_user()
    entry = database.AsyncRaceEntry.entry_for(room, user)
    if entry is None:
        raise error.NotAuthorizedForActionError

    old_state = entry.user_status()
    new_state = AsyncRaceRoomUserStatus(new_state)

    now = lib.datetime_now()

    things_to_save = [entry]

    match (old_state, new_state):
        case (AsyncRaceRoomUserStatus.JOINED, AsyncRaceRoomUserStatus.STARTED):
            entry.start_datetime = now
            # FIXME: limit distance of start date from join date

        case (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.JOINED):
            # Undoing pressing "Start"
            entry.start_datetime = None

        case (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.PAUSED):
            # Pressing Pause
            if not room.allow_pause:
                raise error.InvalidActionError("Pausing not allowed")

            AsyncRaceEntryPause.create(entry=entry, start=now)
            entry.paused = True

        case (AsyncRaceRoomUserStatus.PAUSED, AsyncRaceRoomUserStatus.STARTED):
            # Undoing pressing "Pause"
            pause = AsyncRaceEntryPause.active_pause(entry)
            pause.end = now
            things_to_save.append(pause)
            entry.paused = False

        case (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.FINISHED):
            # Pressing Finish
            entry.finish_datetime = now

        case (AsyncRaceRoomUserStatus.FINISHED, AsyncRaceRoomUserStatus.STARTED):
            # Undoing pressing "Finish"
            entry.finish_datetime = None

        case (AsyncRaceRoomUserStatus.STARTED | AsyncRaceRoomUserStatus.FINISHED, AsyncRaceRoomUserStatus.FORFEITED):
            # Pressing Forfeit
            entry.forfeit = True

        case (AsyncRaceRoomUserStatus.FORFEITED, AsyncRaceRoomUserStatus.STARTED | AsyncRaceRoomUserStatus.FINISHED):
            # Undoing pressing Forfeit
            entry.forfeit = False

        case (_, _):
            raise error.InvalidActionError("Unsupported state transition")

    with database.db.atomic():
        database.AsyncRaceAuditEntry.create(
            room=room, user=sa.get_current_user(), message=f"Changed state from {old_state.value} to {new_state.value}"
        )
        for it in things_to_save:
            it.save()

    return room.create_session_entry(sa).as_json


def get_own_proof(sa: ServerApp, room_id: int) -> tuple[str, str]:
    """
    This endpoint allows a user to request their own submission notes and proof url.
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    user = sa.get_current_user()
    entry = database.AsyncRaceEntry.entry_for(room, user)
    if entry is None:
        raise error.NotAuthorizedForActionError

    if entry.user_status() != AsyncRaceRoomUserStatus.FINISHED:
        raise error.InvalidActionError("Only possible to submit proof after finishing")

    database.AsyncRaceAuditEntry.create(
        room=room, user=sa.get_current_user(), message="Requested own submission notes and proof."
    )

    return entry.submission_notes, entry.proof_url


def submit_proof(sa: ServerApp, room_id: int, submission_notes: str, proof_url: str) -> None:
    """
    This endpoint allows a user to record submission notes and a link to proof for their run.
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    user = sa.get_current_user()
    entry = database.AsyncRaceEntry.entry_for(room, user)
    if entry is None:
        raise error.NotAuthorizedForActionError

    if entry.user_status() != AsyncRaceRoomUserStatus.FINISHED:
        raise error.InvalidActionError("Only possible to submit proof after finishing")

    database.AsyncRaceAuditEntry.create(
        room=room, user=sa.get_current_user(), message="Updated submission notes and proof."
    )

    entry.submission_notes = submission_notes
    entry.proof_url = proof_url
    entry.save()


def setup_app(sa: ServerApp) -> None:
    sa.on("async_race_list_rooms", list_rooms, with_header_check=True)
    sa.on("async_race_create_room", create_room, with_header_check=True)
    sa.on("async_race_change_room_settings", change_room_settings, with_header_check=True)
    sa.on("async_race_get_room", get_room, with_header_check=True)
    sa.on("async_race_refresh_room", refresh_room, with_header_check=True)
    sa.on("async_race_get_leaderboard", get_leaderboard, with_header_check=True)
    sa.on("async_race_get_layout", get_layout, with_header_check=True)
    sa.on("async_race_get_audit_log", get_audit_log, with_header_check=True)
    sa.on("async_race_admin_get_admin_data", admin_get_admin_data, with_header_check=True)
    sa.on("async_race_admin_update_entries", admin_update_entries, with_header_check=True)
    sa.on("async_race_join_and_export", join_and_export, with_header_check=True)
    sa.on("async_race_change_state", change_state, with_header_check=True)
    sa.on("async_race_get_own_proof", get_own_proof, with_header_check=True)
    sa.on("async_race_submit_proof", submit_proof, with_header_check=True)
