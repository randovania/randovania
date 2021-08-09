import base64
import hashlib
import json
import logging
import typing
from typing import Optional, List, Tuple

import flask
import flask_socketio
import peewee

from randovania.bitpacking import bitpacking
from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout import game_to_class
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.preset_migration import VersionedPreset
from randovania.network_common.admin_actions import SessionAdminGlobalAction, SessionAdminUserAction
from randovania.network_common.binary_formats import BinaryInventory
from randovania.network_common.error import (WrongPassword, NotAuthorizedForAction, InvalidAction)
from randovania.network_common.pickup_serializer import BitPackPickupEntry
from randovania.network_common.session_state import GameSessionState
from randovania.server import database
from randovania.server.database import (GameSession, GameSessionMembership, GameSessionTeamAction, GameSessionPreset,
                                        GameSessionAudit)
from randovania.server.lib import logger
from randovania.server.server_app import ServerApp


def list_game_sessions(sio: ServerApp):
    return [
        session.create_list_entry()
        for session in GameSession.select()
    ]


def create_game_session(sio: ServerApp, session_name: str):
    current_user = sio.get_current_user()

    with database.db.atomic():
        new_session: GameSession = GameSession.create(
            name=session_name,
            password=None,
            creator=current_user,
        )
        GameSessionPreset.create(session=new_session, row=0,
                                 preset=json.dumps(PresetManager(None).default_preset.as_json))
        membership = GameSessionMembership.create(
            user=sio.get_current_user(), session=new_session,
            row=0, admin=True, connection_state="Online, Unknown")

    sio.join_game_session(membership)
    return new_session.create_session_entry()


def join_game_session(sio: ServerApp, session_id: int, password: Optional[str]):
    session: GameSession = GameSession.get_by_id(session_id)

    if session.password is not None:
        if password is None or _hash_password(password) != session.password:
            raise WrongPassword()
    elif password is not None:
        raise WrongPassword()

    membership = GameSessionMembership.get_or_create(user=sio.get_current_user(), session=session,
                                                     defaults={"row": None, "admin": False,
                                                               "connection_state": "Online, Unknown"})[0]

    _emit_session_meta_update(session)
    sio.join_game_session(membership)

    return session.create_session_entry()


def disconnect_game_session(sio: ServerApp, session_id: int):
    current_user = sio.get_current_user()
    try:
        current_membership = GameSessionMembership.get_by_ids(current_user.id, session_id)
        current_membership.connection_state = "Offline"
        current_membership.save()
        _emit_session_meta_update(current_membership.session)
    except peewee.DoesNotExist:
        pass
    sio.leave_game_session()


def _verify_has_admin(sio: ServerApp, session_id: int, admin_user_id: Optional[int],
                      *, allow_when_no_admins: bool = False) -> None:
    """
    Checks if the logged user can do admin operations to the given session,
    :param session_id: The GameSessions id
    :param admin_user_id: An user id that is exceptionally authorized for this
    :param allow_when_no_admins: This action is authorized for non-admins if there are no admins.
    :return:
    """
    current_user = sio.get_current_user()
    try:
        current_membership = GameSessionMembership.get_by_ids(current_user.id, session_id)
    except peewee.DoesNotExist:
        raise NotAuthorizedForAction()

    if not (current_membership.admin or (admin_user_id is not None and current_user.id == admin_user_id)):
        if allow_when_no_admins and GameSessionMembership.select().where(
                GameSessionMembership.session == session_id, GameSessionMembership.admin == True).count() == 0:
            return
        raise NotAuthorizedForAction()


def _verify_in_setup(session: GameSession):
    if session.state != GameSessionState.SETUP:
        raise InvalidAction("Session is not in setup")


def _verify_no_layout_description(session: GameSession):
    if session.layout_description_json is not None:
        raise InvalidAction("Session has a generated game")


def _get_preset(preset_json: dict) -> VersionedPreset:
    try:
        preset = VersionedPreset(preset_json)
        preset.get_preset()  # test if valid
        return preset
    except Exception as e:
        raise InvalidAction(f"invalid preset: {e}")


def _emit_session_meta_update(session: GameSession):
    flask_socketio.emit("game_session_meta_update", session.create_session_entry(), room=f"game-session-{session.id}")


def _emit_session_actions_update(session: GameSession):
    flask_socketio.emit("game_session_actions_update", session.describe_actions(), room=f"game-session-{session.id}")


def _emit_session_audit_update(session: GameSession):
    flask_socketio.emit("game_session_audit_update", session.get_audit_log(), room=f"game-session-{session.id}")


def _add_audit_entry(sio: ServerApp, session: GameSession, message: str):
    GameSessionAudit.create(
        session=session,
        user=sio.get_current_user(),
        message=message
    )
    _emit_session_audit_update(session)


def game_session_request_update(sio: ServerApp, session_id: int):
    current_user = sio.get_current_user()
    session: GameSession = GameSession.get_by_id(session_id)
    membership = GameSessionMembership.get_by_ids(current_user.id, session_id)

    _emit_session_meta_update(session)
    if session.layout_description is not None:
        _emit_session_actions_update(session)

    if not membership.is_observer and session.state != GameSessionState.SETUP:
        _emit_game_session_pickups_update(sio, membership)

    _emit_session_audit_update(session)


def _create_row(sio: ServerApp, session: GameSession, preset_json: dict):
    _verify_has_admin(sio, session.id, None)
    _verify_in_setup(session)
    _verify_no_layout_description(session)
    preset = _get_preset(preset_json)

    new_row_id = session.num_rows
    with database.db.atomic():
        logger().info(f"Session {session.id}: Creating row {new_row_id}.")
        GameSessionPreset.create(session=session, row=new_row_id,
                                 preset=json.dumps(preset.as_json))


def _change_row(sio: ServerApp, session: GameSession, arg: Tuple[int, dict]):
    if len(arg) != 2:
        raise InvalidAction("Missing arguments.")
    row_id, preset_json = arg
    _verify_has_admin(sio, session.id, sio.get_current_user().id)
    _verify_in_setup(session)
    _verify_no_layout_description(session)
    preset = _get_preset(preset_json)

    if preset.game not in session.allowed_games:
        raise InvalidAction(f"Only {preset.game} preset not allowed.")

    try:
        with database.db.atomic():
            preset_row = GameSessionPreset.get(GameSessionPreset.session == session,
                                               GameSessionPreset.row == row_id)
            preset_row.preset = json.dumps(preset.as_json)
            logger().info(f"Session {session.id}: Changing row {row_id}.")
            preset_row.save()

    except peewee.DoesNotExist:
        raise InvalidAction(f"invalid row: {row_id}")


def _delete_row(sio: ServerApp, session: GameSession, row_id: int):
    _verify_has_admin(sio, session.id, None)
    _verify_in_setup(session)
    _verify_no_layout_description(session)

    if session.num_rows < 2:
        raise InvalidAction("Can't delete row when there's only one")

    if row_id != session.num_rows - 1:
        raise InvalidAction(f"Can only delete the last row")

    with database.db.atomic():
        logger().info(f"Session {session.id}: Deleting {row_id}.")
        GameSessionPreset.delete().where(GameSessionPreset.session == session,
                                         GameSessionPreset.row == row_id).execute()
        GameSessionMembership.update(row=None).where(
            GameSessionMembership.session == session.id,
            GameSessionMembership.row == row_id,
        ).execute()


def _update_layout_generation(sio: ServerApp, session: GameSession, active: bool):
    _verify_has_admin(sio, session.id, None)
    _verify_in_setup(session)

    if active:
        if session.generation_in_progress is None:
            session.generation_in_progress = sio.get_current_user()
        else:
            raise InvalidAction(f"Generation already in progress by {session.generation_in_progress.name}.")
    else:
        session.generation_in_progress = None

    logger().info(f"Session {session.id}: Making generation in progress to {session.generation_in_progress}.")
    session.save()


def _change_layout_description(sio: ServerApp, session: GameSession, description_json: Optional[dict]):
    _verify_has_admin(sio, session.id, None)
    _verify_in_setup(session)
    rows_to_update = []

    if description_json is None:
        description = None
    else:
        if session.generation_in_progress != sio.get_current_user():
            if session.generation_in_progress is None:
                raise InvalidAction(f"Not waiting for a layout.")
            else:
                raise InvalidAction(f"Waiting for a layout from {session.generation_in_progress.name}.")

        _verify_no_layout_description(session)
        description = LayoutDescription.from_json_dict(description_json)
        permalink = description.permalink
        if permalink.player_count != session.num_rows:
            raise InvalidAction(f"Description is for a {permalink.player_count} players,"
                                f" while the session is for {session.num_rows}.")

        for permalink_preset, preset_row in zip(permalink.presets.values(), session.presets):
            preset_row = typing.cast(GameSessionPreset, preset_row)
            if _get_preset(json.loads(preset_row.preset)).get_preset() != permalink_preset:
                preset = VersionedPreset.with_preset(permalink_preset)
                if preset.game not in session.allowed_games:
                    raise InvalidAction(f"Only {preset.game} preset not allowed.")
                preset_row.preset = json.dumps(preset.as_json)
                rows_to_update.append(preset_row)

    with database.db.atomic():
        for preset_row in rows_to_update:
            preset_row.save()

        session.generation_in_progress = None
        session.layout_description = description
        session.save()
        _add_audit_entry(sio, session,
                         "Removed generated game" if description is None
                         else f"Set game to {description.shareable_word_hash}")


def _download_layout_description(sio: ServerApp, session: GameSession):
    try:
        # You must be a session member to do get the spoiler
        GameSessionMembership.get_by_ids(sio.get_current_user().id, session.id)
    except peewee.DoesNotExist:
        raise NotAuthorizedForAction()

    if session.layout_description_json is None:
        raise InvalidAction("Session does not contain a game")

    if not session.layout_description.permalink.spoiler:
        raise InvalidAction("Session does not contain a spoiler")

    _add_audit_entry(sio, session, f"Requested the spoiler log")
    return session.layout_description_json


def _start_session(sio: ServerApp, session: GameSession):
    _verify_has_admin(sio, session.id, None)
    _verify_in_setup(session)
    if session.layout_description_json is None:
        raise InvalidAction("Unable to start session, no game is available.")

    num_players = GameSessionMembership.select().where(GameSessionMembership.session == session,
                                                       GameSessionMembership.row != None).count()
    expected_players = session.num_rows
    if num_players != expected_players:
        raise InvalidAction(f"Unable to start session, there are {num_players} but expected {expected_players} "
                            f"({session.num_rows} x {session.num_teams}).")

    session.state = GameSessionState.IN_PROGRESS
    logger().info(f"Session {session.id}: Starting session.")
    session.save()
    _add_audit_entry(sio, session, f"Started session")


def _finish_session(sio: ServerApp, session: GameSession):
    _verify_has_admin(sio, session.id, None)
    if session.state != GameSessionState.IN_PROGRESS:
        raise InvalidAction("Session is not in progress")

    session.state = GameSessionState.FINISHED
    logger().info(f"Session {session.id}: Finishing session.")
    session.save()
    _add_audit_entry(sio, session, f"Finished session")


def _reset_session(sio: ServerApp, session: GameSession):
    raise InvalidAction("Restart session is not yet implemented.")


def _hash_password(password: str) -> str:
    return hashlib.blake2s(password.encode("utf-8")).hexdigest()


def _change_password(sio: ServerApp, session: GameSession, password: str):
    _verify_has_admin(sio, session.id, None)

    session.password = _hash_password(password)
    logger().info(f"Session {session.id}: Changing password.")
    session.save()
    _add_audit_entry(sio, session, f"Changed password")


def game_session_admin_session(sio: ServerApp, session_id: int, action: str, arg):
    action: SessionAdminGlobalAction = SessionAdminGlobalAction(action)
    session: database.GameSession = database.GameSession.get_by_id(session_id)

    if action == SessionAdminGlobalAction.CREATE_ROW:
        _create_row(sio, session, arg)

    elif action == SessionAdminGlobalAction.CHANGE_ROW:
        _change_row(sio, session, arg)

    elif action == SessionAdminGlobalAction.DELETE_ROW:
        _delete_row(sio, session, arg)

    elif action == SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION:
        _update_layout_generation(sio, session, arg)

    elif action == SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION:
        _change_layout_description(sio, session, arg)

    elif action == SessionAdminGlobalAction.DOWNLOAD_LAYOUT_DESCRIPTION:
        return _download_layout_description(sio, session)

    elif action == SessionAdminGlobalAction.START_SESSION:
        _start_session(sio, session)

    elif action == SessionAdminGlobalAction.FINISH_SESSION:
        _finish_session(sio, session)

    elif action == SessionAdminGlobalAction.RESET_SESSION:
        _reset_session(sio, session)

    elif action == SessionAdminGlobalAction.CHANGE_PASSWORD:
        _change_password(sio, session, arg)

    elif action == SessionAdminGlobalAction.DELETE_SESSION:
        logger().info(f"Session {session.id}: Deleting session.")
        session.delete_instance(recursive=True)

    _emit_session_meta_update(session)


def _find_empty_row(session: GameSession) -> int:
    possible_rows = set(range(session.num_rows))
    for member in GameSessionMembership.non_observer_members(session):
        possible_rows.remove(member.row)

    for empty_row in sorted(possible_rows):
        return empty_row
    raise InvalidAction("Session is full")


def game_session_admin_player(sio: ServerApp, session_id: int, user_id: int, action: str, arg):
    _verify_has_admin(sio, session_id, user_id)
    action: SessionAdminUserAction = SessionAdminUserAction(action)

    session: GameSession = database.GameSession.get_by_id(session_id)
    membership = GameSessionMembership.get_by_ids(user_id, session_id)

    if action == SessionAdminUserAction.KICK:
        _add_audit_entry(sio, session,
                         f"Kicked {membership.effective_name}" if membership.user != sio.get_current_user()
                         else "Left session")
        membership.delete_instance()
        if not list(session.players):
            session.delete_instance(recursive=True)
            logger().info(f"Session {session_id}. Kicking user {user_id} and deleting session.")
        else:
            logger().info(f"Session {session_id}. Kicking user {user_id}.")

    elif action == SessionAdminUserAction.MOVE:
        offset: int = arg
        if membership.is_observer is None:
            raise InvalidAction("Player is an observer")

        new_row = membership.row + offset
        if new_row < 0:
            raise InvalidAction("New position is negative")
        if new_row >= session.num_rows:
            raise InvalidAction("New position is beyond num of rows")

        team_members = [None] * session.num_rows
        for member in GameSessionMembership.non_observer_members(session):
            team_members[member.row] = member

        while (0 <= new_row < session.num_rows) and team_members[new_row] is not None:
            new_row += offset

        if new_row < 0 or new_row >= session.num_rows:
            raise InvalidAction("No empty slots found in this direction")

        with database.db.atomic():
            logger().info(f"Session {session_id}, User {user_id}. "
                          f"Performing {action}, new row is {new_row}, from {membership.row}.")
            membership.row = new_row
            membership.save()

    elif action == SessionAdminUserAction.SWITCH_IS_OBSERVER:
        if membership.is_observer:
            membership.row = _find_empty_row(session)
        else:
            membership.row = None
        logger().info(f"Session {session_id}, User {user_id}. Performing {action}, new row is {membership.row}.")
        membership.save()

    elif action == SessionAdminUserAction.SWITCH_ADMIN:
        # Must be admin for this
        _verify_has_admin(sio, session_id, None, allow_when_no_admins=True)
        num_admins = GameSessionMembership.select().where(GameSessionMembership.session == session_id,
                                                          GameSessionMembership.admin == True).count()

        if membership.admin and num_admins <= 1:
            raise InvalidAction("can't demote the only admin")

        membership.admin = not membership.admin
        _add_audit_entry(sio, session, f"Made {membership.effective_name} {'' if membership.admin else 'not '}an admin")
        logger().info(f"Session {session_id}, User {user_id}. Performing {action}, new status is {membership.admin}.")
        membership.save()

    elif action == SessionAdminUserAction.CREATE_PATCHER_FILE:
        player_names = {i: f"Player {i + 1}" for i in range(session.num_rows)}

        for member in GameSessionMembership.non_observer_members(session):
            player_names[member.row] = member.effective_name

        layout_description = session.layout_description
        players_config = PlayersConfiguration(
            player_index=membership.row,
            player_names=player_names,
        )
        preset = layout_description.permalink.get_preset(players_config.player_index)
        cosmetic_patches = game_to_class.GAME_TO_COSMETIC[preset.game].from_json(arg)
        patcher = sio.patcher_provider.patcher_for_game(preset.game)

        _add_audit_entry(sio, session, f"Made an ISO for row {membership.row + 1}")

        return patcher.create_patch_data(session.layout_description,
                                         players_config,
                                         cosmetic_patches)

    elif action == SessionAdminUserAction.ABANDON:
        # FIXME
        raise InvalidAction("Abandon is NYI")

    _emit_session_meta_update(session)


def _query_for_actions(membership: GameSessionMembership) -> peewee.ModelSelect:
    return GameSessionTeamAction.select().where(
        GameSessionTeamAction.provider_row != membership.row,
        GameSessionTeamAction.session == membership.session,
        GameSessionTeamAction.receiver_row == membership.row,
    ).order_by(GameSessionTeamAction.time.asc())


def _base64_encode_pickup(pickup: PickupEntry, resource_database: ResourceDatabase) -> str:
    encoded_pickup = bitpacking.pack_value(BitPackPickupEntry(pickup, resource_database))
    return base64.b85encode(encoded_pickup).decode("utf-8")


def _collect_location(session: GameSession, membership: GameSessionMembership,
                      description: LayoutDescription,
                      pickup_location: int) -> Optional[int]:
    """
    Collects the pickup in the given location. Returns
    :param session:
    :param membership:
    :param description:
    :param pickup_location:
    :return: The rewarded player if some player must be updated of the fact.
    """
    player_row: int = membership.row
    pickup_target = _get_pickup_target(description, player_row, pickup_location)

    def log(msg):
        logger().info(f"Session {session.id}, Row {membership.row} found item at {pickup_location}. {msg}")

    if pickup_target is None:
        log(f"It's an ETM.")
        return None

    if pickup_target.player == membership.row:
        log(f"It's a {pickup_target.pickup.name} for themselves.")
        return None

    try:
        GameSessionTeamAction.create(
            session=session,
            provider_row=membership.row,
            provider_location_index=pickup_location,
            receiver_row=pickup_target.player,
        )
    except peewee.IntegrityError:
        # Already exists and it's for another player, no inventory update needed
        log(f"It's a {pickup_target.pickup.name} for {pickup_target.player}, but it was already collected.")
        return None

    log(f"It's a {pickup_target.pickup.name} for {pickup_target.player}.")
    return pickup_target.player


def game_session_collect_locations(sio: ServerApp, session_id: int, pickup_locations: Tuple[int, ...]):
    current_user = sio.get_current_user()
    session: GameSession = database.GameSession.get_by_id(session_id)
    membership = GameSessionMembership.get_by_ids(current_user.id, session_id)

    if session.state != GameSessionState.IN_PROGRESS:
        raise InvalidAction("Unable to collect locations of sessions that aren't in progress")

    if membership.is_observer:
        raise InvalidAction("Observers can't collect locations")

    logger().info(f"Session {session.id}, Row {membership.row} found items {pickup_locations}")
    description = session.layout_description

    receiver_players = set()
    for location in pickup_locations:
        receiver_player = _collect_location(session, membership, description, location)
        if receiver_player is not None:
            receiver_players.add(receiver_player)

    if not receiver_players:
        return

    for receiver_player in receiver_players:
        try:
            receiver_membership = GameSessionMembership.get_by_session_position(session, row=receiver_player)
            _emit_game_session_pickups_update(sio, receiver_membership)
        except peewee.DoesNotExist:
            pass
    _emit_session_actions_update(session)


def _get_resource_database(description: LayoutDescription, player: int) -> ResourceDatabase:
    return default_database.resource_database_for(description.permalink.get_preset(player).game)


def _get_pickup_target(description: LayoutDescription, provider: int, location: int) -> Optional[PickupTarget]:
    pickup_assignment = description.all_patches[provider].pickup_assignment
    return pickup_assignment.get(PickupIndex(location))


def _emit_game_session_pickups_update(sio: ServerApp, membership: GameSessionMembership):
    session: GameSession = membership.session

    if session.state == GameSessionState.SETUP:
        raise RuntimeError("Unable to emit pickups during SETUP")

    if membership.is_observer:
        raise RuntimeError("Unable to emit pickups for observers")

    description = session.layout_description
    row_to_member_name = {
        member.row: member.effective_name
        for member in GameSessionMembership.non_observer_members(session)
    }

    resource_database = _get_resource_database(description, membership.row)

    result = []
    actions: List[GameSessionTeamAction] = list(_query_for_actions(membership))
    for action in actions:
        pickup_target = _get_pickup_target(description, action.provider_row, action.provider_location_index)

        if pickup_target is None:
            logging.error(f"Action {action} has a location index with nothing.")
            result.append(None)
        else:
            name = row_to_member_name.get(action.provider_row, f"Player {action.provider_row + 1}")
            result.append({
                "provider_name": name,
                "pickup": _base64_encode_pickup(pickup_target.pickup, resource_database),
            })

    logger().info(f"Session {session.id}, Row {membership.row} "
                  f"notifying {resource_database.game_enum.value} of {len(result)} pickups.")

    data = {
        "game": resource_database.game_enum.value,
        "pickups": result,
    }
    flask_socketio.emit("game_session_pickups_update", data, room=f"game-session-{session.id}-{membership.user.id}")


def game_session_self_update(sio: ServerApp, session_id: int, inventory: bytes, game_connection_state: str):
    current_user = sio.get_current_user()
    membership = GameSessionMembership.get_by_ids(current_user.id, session_id)

    old_state = membership.connection_state
    # old_inventory = membership.inventory

    membership.connection_state = f"Online, {game_connection_state}"
    membership.inventory = inventory
    membership.save()
    if old_state != membership.connection_state:
        _emit_session_meta_update(membership.session)


def report_user_disconnected(sio: ServerApp, user_id: int, log):
    memberships: List[GameSessionMembership] = list(GameSessionMembership.select().where(
        GameSessionMembership.user == user_id))

    log.info(f"User {user_id} is disconnected, disconnecting from sessions: {memberships}")
    sessions_to_update = []

    for membership in memberships:
        if membership.connection_state != "Offline":
            membership.connection_state = "Offline"
            sessions_to_update.append(membership.session)
            membership.save()

    for session in sessions_to_update:
        _emit_session_meta_update(session)


def setup_app(sio: ServerApp):
    sio.on("list_game_sessions", list_game_sessions)
    sio.on("create_game_session", create_game_session)
    sio.on("join_game_session", join_game_session)
    sio.on("disconnect_game_session", disconnect_game_session)
    sio.on("game_session_request_update", game_session_request_update)
    sio.on("game_session_admin_session", game_session_admin_session)
    sio.on("game_session_admin_player", game_session_admin_player)
    sio.on("game_session_collect_locations", game_session_collect_locations)
    sio.on("game_session_self_update", game_session_self_update)

    @sio.admin_route("/sessions")
    def admin_sessions(user):
        lines = []
        for session in GameSession.select().order_by(GameSession.creation_date):
            lines.append("<tr><td><a href='{}'>{}</a></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                flask.url_for('admin_session', session_id=session.id),
                session.name,
                session.creator.name,
                session.creation_date,
                session.state,
                len(session.players),
            ))

        return ("<table border='1'>"
                "<tr><th>Name</th><th>Creator</th><th>Creation Date</th><th>State</th><th>Num Players</th></tr>"
                "{}</table>").format("".join(lines))

    @sio.admin_route("/session/<session_id>")
    def admin_session(user, session_id):
        session: GameSession = GameSession.get_by_id(session_id)

        rows = []
        presets = session.all_presets

        for player in session.players:
            player = typing.cast(GameSessionMembership, player)
            if player.is_observer:
                rows.append([
                    player.effective_name,
                    "Observer",
                    "",
                ])
            else:
                preset = presets[player.row]
                db = default_database.resource_database_for(preset.game)

                inventory = []
                if player.inventory is not None:
                    for item in BinaryInventory.parse(player.inventory):
                        if item["amount"] + item["capacity"] > 0:
                            inventory.append("{} x{}/{}".format(
                                db.get_item(item["index"]).long_name,
                                item["amount"], item["capacity"]
                            ))

                rows.append([
                    player.effective_name,
                    preset.name,
                    ", ".join(inventory),
                ])

        header = ["Name", "Preset", "Inventory"]

        return "<table border='1'><tr>{}</tr>{}</table>".format(
            "".join(f"<th>{h}</th>" for h in header),
            "".join("<tr>{}</tr>".format("".join(f"<td>{h}</td>" for h in r)) for r in rows),
        )
