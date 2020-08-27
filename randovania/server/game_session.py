import base64
import collections
import json
import logging
from typing import Optional, List

import flask_socketio
import peewee

from randovania.bitpacking import bitpacking
from randovania.game_description import data_reader
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.prime import patcher_file
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.game_patches_serializer import BitPackPickupEntry
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.preset import Preset
from randovania.network_common.admin_actions import SessionAdminGlobalAction, SessionAdminUserAction
from randovania.network_common.error import WrongPassword, \
    NotAuthorizedForAction, InvalidAction
from randovania.server import database
from randovania.server.database import GameSession, GameSessionMembership, GameSessionTeamAction, \
    GameSessionPreset
from randovania.server.lib import logger
from randovania.server.server_app import ServerApp


def list_game_sessions(sio: ServerApp):
    return [
        session.create_list_entry()
        for session in GameSession.select()
    ]


def create_game_session(sio: ServerApp, session_name: str):
    with database.db.atomic():
        new_session = GameSession.create(
            name=session_name,
            password=None,
            num_teams=1,
        )
        GameSessionPreset.create(session=new_session, row=0,
                                 preset=json.dumps(PresetManager(None).default_preset.as_json))
        membership = GameSessionMembership.create(
            user=sio.get_current_user(), session=new_session,
            row=0, team=0, admin=True)

    sio.join_session(membership)
    return new_session.create_session_entry()


def join_game_session(sio: ServerApp, session_id: str, password: Optional[str]):
    session = GameSession.get_by_id(session_id)
    if password != session.password:
        raise WrongPassword()

    membership = GameSessionMembership.get_or_create(user=sio.get_current_user(), session=session,
                                                     defaults={"row": 0, "team": None, "admin": False})[0]

    _emit_session_update(session)
    sio.join_session(membership)

    return session.create_session_entry()


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


def _verify_not_in_game(session: GameSession):
    if session.in_game:
        raise InvalidAction("Session is in-game")


def _get_preset(preset_json: dict) -> Preset:
    try:
        return Preset.from_json_dict(preset_json)
    except Exception as e:
        raise InvalidAction(f"invalid preset: {e}")


def _emit_session_update(session: GameSession):
    flask_socketio.emit("game_session_update", session.create_session_entry(), room=f"game-session-{session.id}")


def game_session_admin_session(sio: ServerApp, session_id: int, action: str, arg):
    _verify_has_admin(sio, session_id, None)
    action: SessionAdminGlobalAction = SessionAdminGlobalAction(action)

    session: database.GameSession = database.GameSession.get_by_id(session_id)

    if action == SessionAdminGlobalAction.CREATE_ROW:
        preset_json: dict = arg
        _verify_not_in_game(session)
        preset = _get_preset(preset_json)

        new_row_id = session.num_rows
        with database.db.atomic():
            GameSessionPreset.create(session=session, row=new_row_id,
                                     preset=json.dumps(preset.as_json))
            session.reset_layout_description()

    elif action == SessionAdminGlobalAction.CHANGE_ROW:
        if len(arg) != 2:
            raise InvalidAction("Missing arguments.")

        row_id, preset_json = arg
        _verify_not_in_game(session)
        preset = _get_preset(preset_json)

        try:
            with database.db.atomic():
                preset_row = GameSessionPreset.get(GameSessionPreset.session == session,
                                                   GameSessionPreset.row == row_id)
                preset_row.preset = json.dumps(preset.as_json)
                preset_row.save()
                session.reset_layout_description()

        except peewee.DoesNotExist:
            raise InvalidAction(f"invalid row: {row_id}")

    elif action == SessionAdminGlobalAction.DELETE_ROW:
        row_id: int = arg
        _verify_not_in_game(session)

        if session.num_rows < 1:
            raise InvalidAction("Can't delete row when there's only one")

        if row_id != session.num_rows - 1:
            raise InvalidAction(f"Can only delete the last row")

        with database.db.atomic():
            GameSessionPreset.delete().where(GameSessionPreset.session == session,
                                             GameSessionPreset.row == row_id).execute()
            GameSessionMembership.update(team=None).where(
                GameSessionMembership.session == session.id,
                GameSessionMembership.row == row_id,
            ).execute()
            session.reset_layout_description()

    elif action == SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION:
        description_json: dict = arg
        _verify_not_in_game(session)
        description = LayoutDescription.from_json_dict(description_json)

        permalink = description.permalink
        if list(permalink.presets.values()) != session.all_presets:
            raise InvalidAction("Description presets doesn't match the session presets")

        session.layout_description = description
        session.save()

    elif action == SessionAdminGlobalAction.START_SESSION:
        _verify_not_in_game(session)
        if session.layout_description is None:
            raise InvalidAction("Unable to start session, no game is available.")

        num_players = GameSessionMembership.select().where(GameSessionMembership.session == session,
                                                           GameSessionMembership.team != None).count()
        expected_players = session.num_rows * session.num_teams
        if num_players != expected_players:
            raise InvalidAction(f"Unable to start session, there are {num_players} but expected {expected_players} "
                                f"({session.num_rows} x {session.num_teams}).")

        session.in_game = True
        session.save()

    _emit_session_update(session)


def _switch_team(session: GameSession, membership: GameSessionMembership, new_team: Optional[int]):
    other_membership: Optional[GameSessionMembership]

    if new_team is None:
        expected_row = 0
    else:
        if not (0 <= new_team < session.num_teams):
            raise InvalidAction("New team does not exist")

        expected_row = 0
        for possible_slot in GameSessionMembership.members_for_team(session, new_team):
            if expected_row != possible_slot.row:
                break
            else:
                expected_row += 1

        if expected_row >= session.num_rows:
            raise InvalidAction("Team is full")

    # Delete empty teams
    all_members: List[GameSessionMembership] = list(GameSessionMembership.select().where(
        GameSessionMembership.session == session))

    member_count_per_team = collections.defaultdict(int)
    for member in all_members:
        if member.team is not None:
            member_count_per_team[member.team] += 1

    member_count_per_team[membership.team] -= 1
    if new_team is not None:
        member_count_per_team[new_team] += 1

    new_num_teams = session.num_teams
    while new_num_teams > 1 and member_count_per_team[new_num_teams - 1] == 0:
        new_num_teams -= 1

    with database.db.atomic():
        session.num_teams = new_num_teams
        session.save()
        membership.row = expected_row
        membership.team = new_team
        membership.save()


def game_session_admin_player(sio: ServerApp, session_id: int, user_id: int, action: str, arg):
    _verify_has_admin(sio, session_id, user_id)
    action: SessionAdminUserAction = SessionAdminUserAction(action)

    session: GameSession = database.GameSession.get_by_id(session_id)
    membership = GameSessionMembership.get_by_ids(user_id, session_id)

    if action == SessionAdminUserAction.KICK:
        target_player: int = arg
        # FIXME
        raise InvalidAction("Kick is NYI")

    elif action == SessionAdminUserAction.MOVE:
        offset: int = arg
        new_row = membership.row + offset

        if new_row < 0:
            raise InvalidAction("New position is negative")
        if new_row >= session.num_rows:
            raise InvalidAction("New position is beyond num of rows")
        if membership.team is None:
            raise InvalidAction("Player has no team")

        team_members = [None] * session.num_rows
        for member in GameSessionMembership.members_for_team(session, team=membership.team):
            team_members[member.row] = member

        while (0 <= new_row < session.num_rows) and team_members[new_row] is not None:
            new_row += offset

        if new_row < 0 or new_row >= session.num_rows:
            raise InvalidAction("No empty slots found in this direction")

        with database.db.atomic():
            membership.row = new_row
            membership.save()

    elif action == SessionAdminUserAction.SWITCH_TO_NEW_TEAM:
        with database.db.atomic():
            membership.row = 0
            membership.team = session.num_teams
            session.num_teams += 1

            session.save()
            membership.save()

    elif action == SessionAdminUserAction.SWITCH_TEAM:
        _switch_team(session, membership, arg)

    elif action == SessionAdminUserAction.SWITCH_ADMIN:
        # Must be admin for this
        _verify_has_admin(sio, session_id, None, allow_when_no_admins=True)
        num_admins = GameSessionMembership.select().where(GameSessionMembership.session == session_id,
                                                          GameSessionMembership.admin == True).count()

        if membership.admin and num_admins <= 1:
            raise InvalidAction("can't demote the only admin")

        membership.admin = not membership.admin
        membership.save()

    elif action == SessionAdminUserAction.CREATE_PATCHER_FILE:
        cosmetic_patches = CosmeticPatches.from_json_dict(arg)
        player_names = {i: f"Player {i + 1}" for i in range(session.num_rows)}

        for member in GameSessionMembership.members_for_team(session, membership.team):
            player_names[member.row] = member.effective_name

        players_config = PlayersConfiguration(
            player_index=membership.row,
            player_names=player_names,
        )
        return patcher_file.create_patcher_file(session.layout_description,
                                                players_config,
                                                cosmetic_patches)

    elif action == SessionAdminUserAction.ABANDON:
        # FIXME
        raise InvalidAction("Abandon is NYI")

    _emit_session_update(session)


def _query_for_actions(membership: GameSessionMembership) -> peewee.ModelSelect:
    return GameSessionTeamAction.select().where(
        GameSessionTeamAction.provider_row != membership.row,
        GameSessionTeamAction.session == membership.session,
        GameSessionTeamAction.team == membership.team,
        GameSessionTeamAction.receiver_row == membership.row,
    ).order_by(GameSessionTeamAction.time.asc())


def _base64_encode_pickup(pickup: PickupEntry, resource_database: ResourceDatabase) -> str:
    encoded_pickup = bitpacking.pack_value(BitPackPickupEntry(pickup, resource_database))
    return base64.b85encode(encoded_pickup).decode("utf-8")


def game_session_collect_pickup(sio: ServerApp, session_id: int, pickup_location: int):
    current_user = sio.get_current_user()
    session: GameSession = database.GameSession.get_by_id(session_id)
    membership = GameSessionMembership.get_by_ids(current_user.id, session_id)

    player_row: int = membership.row

    description = session.layout_description
    pickup_target = _get_pickup_target(description, player_row, pickup_location)

    if pickup_target is None:
        logger().info(
            f"Session {session_id}, Team {membership.team}, Row {membership.row} found item "
            f"at {pickup_location}. It's an ETM.")
        return

    if pickup_target.player == membership.row:
        logger().info(
            f"Session {session_id}, Team {membership.team}, Row {membership.row} found item "
            f"at {pickup_location}. It's a {pickup_target.pickup.name} for themselves.")

        resource_database = _get_resource_database(description, pickup_target.player)
        return _base64_encode_pickup(pickup_target.pickup, resource_database)

    try:
        GameSessionTeamAction.create(
            session=session,
            team=membership.team,
            provider_row=membership.row,
            provider_location_index=pickup_location,
            receiver_row=pickup_target.player,
        )
    except peewee.IntegrityError:
        # Already exists and it's for another player, no inventory update needed
        logger().info(
            f"Session {session_id}, Team {membership.team}, Row {membership.row} found item "
            f"at {pickup_location}. It's a {pickup_target.pickup.name} for {pickup_target.player}, "
            f"but it was already collected.")
        return

    logger().info(f"Session {session_id}, Team {membership.team}, Row {membership.row} found item "
                  f"at {pickup_location}. It's a {pickup_target.pickup.name} for {pickup_target.player}.")

    try:
        receiver_membership = GameSessionMembership.get_by_session_position(
            session, team=membership.team, row=pickup_target.player)
        flask_socketio.emit(
            "game_has_update",
            {
                "session": session_id,
                "team": membership.team,
                "row": pickup_target.player,
            },
            room=f"game-session-{receiver_membership.session.id}-{receiver_membership.user.id}")
    except peewee.DoesNotExist:
        pass


def _get_resource_database(description: LayoutDescription, player: int) -> ResourceDatabase:
    game_data = description.permalink.get_preset(player).layout_configuration.game_data
    return data_reader.read_resource_database(game_data["resource_database"])


def _get_pickup_target(description: LayoutDescription, provider: int, location: int) -> Optional[PickupTarget]:
    pickup_assignment = description.all_patches[provider].pickup_assignment
    return pickup_assignment.get(PickupIndex(location))


def game_session_request_pickups(sio: ServerApp, session_id: int):
    current_user = sio.get_current_user()
    your_membership = GameSessionMembership.get_by_ids(current_user.id, session_id)
    session: GameSession = your_membership.session

    if not session.in_game:
        logger().info(f"Session {session_id}, Team {your_membership.team}, Row {your_membership.row} "
                      f"requested pickups, but session is not in-game.")
        return []

    description = session.layout_description
    row_to_member_name = {
        member.row: member.effective_name
        for member in GameSessionMembership.members_for_team(session, your_membership.team)
    }

    resource_database = _get_resource_database(description, your_membership.row)

    result = []
    actions: List[GameSessionTeamAction] = list(_query_for_actions(your_membership))
    for action in actions:
        pickup_target = _get_pickup_target(description, action.provider_row, action.provider_location_index)

        if pickup_target is None:
            logging.error(f"Action {action} has a location index with nothing.")
            result.append(None)
        else:
            name = row_to_member_name.get(action.provider_row, f"Player {action.provider_row + 1}")
            result.append({
                "message": f"Received {pickup_target.pickup.name} from {name}",
                "pickup": _base64_encode_pickup(pickup_target.pickup, resource_database),
            })

    logger().info(f"Session {session_id}, Team {your_membership.team}, Row {your_membership.row} "
                  f"requested pickups, returning {len(result)} elements.")

    return result


def setup_app(sio: ServerApp):
    sio.on("list_game_sessions", list_game_sessions)
    sio.on("create_game_session", create_game_session)
    sio.on("join_game_session", join_game_session)
    sio.on("game_session_admin_session", game_session_admin_session)
    sio.on("game_session_admin_player", game_session_admin_player)
    sio.on("game_session_collect_pickup", game_session_collect_pickup)
    sio.on("game_session_request_pickups", game_session_request_pickups)
