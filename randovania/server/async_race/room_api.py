import datetime
import json
import typing

from peewee import Case

from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib.json_lib import JsonObject, JsonType
from randovania.network_common import error
from randovania.network_common.async_race_room import AsyncRaceRoomListEntry, AsyncRaceRoomUserStatus, AsyncRaceSettings
from randovania.network_common.game_details import GameDetails
from randovania.network_common.multiplayer_session import (
    MAX_SESSION_NAME_LENGTH,
)
from randovania.server import database
from randovania.server.database import (
    AsyncRaceRoom,
    User,
)
from randovania.server.server_app import ServerApp


def list_rooms(sa: ServerApp, limit: int | None) -> JsonType:
    # Note: this query fails to list any session that has no memberships
    # But that's fine, because these sessions should've been deleted!
    def construct_helper(**args: typing.Any) -> AsyncRaceRoomListEntry:
        args["creation_date"] = datetime.datetime.fromisoformat(args["creation_date"])
        args["start_date"] = datetime.datetime.fromisoformat(args["start_date"])
        args["end_date"] = datetime.datetime.fromisoformat(args["end_date"])
        args["has_password"] = bool(args["has_password"])
        return AsyncRaceRoomListEntry(**args)

    sessions: list[AsyncRaceRoomListEntry] = (
        AsyncRaceRoom.select(
            AsyncRaceRoom.id,
            AsyncRaceRoom.name,
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
        new_room: AsyncRaceRoom = AsyncRaceRoom.create(
            name=settings.name,
            password=settings.password,
            visibility=settings.visibility,
            layout_description_json=layout_bin,
            game_details_json=json.dumps(GameDetails.from_layout(layout).as_json),
            creator=current_user,
            start_date=settings.start_date,
            end_date=settings.end_date,
        )

    return new_room.create_session_entry(current_user).as_json


def change_room_settings(sa: ServerApp, room_id: int, settings_json: JsonObject) -> JsonObject:
    """
    Updates the settings for the given room
    :param sa:
    :param room_id:
    :param settings_json:
    :return:
    """
    current_user = sa.get_current_user()
    settings = AsyncRaceSettings.from_json(settings_json)

    room = AsyncRaceRoom.get_by_id(room_id)

    if room.creator != current_user:
        raise error.NotAuthorizedForActionError

    if not (0 < len(settings.name) <= MAX_SESSION_NAME_LENGTH):
        raise error.InvalidActionError("Invalid session name length")

    room.name = settings.name
    room.start_datetime = settings.start_date
    room.end_datetime = settings.end_date
    room.visibility = settings.visibility
    room.save()

    # TODO: Reusing the `room` after we set start_datetime/end_datetime breaks create_session_entry
    return AsyncRaceRoom.get_by_id(room_id).create_session_entry(current_user).as_json


def get_room(sa: ServerApp, room_id: int) -> JsonType:
    """
    Gets details about the given room id
    :param sa:
    :param room_id: The room to get details for
    :return: A AsyncRaceRoomEntry, json encoded
    """
    room = AsyncRaceRoom.get_by_id(room_id)
    # FIXME: password protected!
    return room.create_session_entry(sa.get_current_user()).as_json


def join_and_export(sa: ServerApp, room_id: int, cosmetic_json: JsonType) -> JsonType:
    """

    :param sa:
    :param room_id: The room to join
    :param cosmetic_json:
    :return:
    """
    # FIXME: password protected!
    user = sa.get_current_user()
    room = AsyncRaceRoom.get_by_id(room_id)

    database.AsyncRaceEntry.get_or_create(
        room=room,
        user=user,
        submission_notes="",
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
    try:
        return data_factory.create_data()
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

    now = datetime.datetime.now(datetime.UTC)

    match (old_state, new_state):
        case (AsyncRaceRoomUserStatus.JOINED, AsyncRaceRoomUserStatus.STARTED):
            entry.start_datetime = now
            # FIXME: limit distance of start date from join date

        case (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.JOINED):
            # Undoing pressing "Start"
            entry.start_datetime = None

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

    database.AsyncRaceAuditEntry.create(
        room=room, user=sa.get_current_user(), message=f"Changed state from {old_state.value} to {new_state.value}"
    )

    entry.save()
    return room.create_session_entry(user).as_json


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
    sa.on("async_race_join_and_export", join_and_export, with_header_check=True)
    sa.on("async_race_change_state", change_state, with_header_check=True)
    sa.on("async_race_submit_proof", submit_proof, with_header_check=True)
