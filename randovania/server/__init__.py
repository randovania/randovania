import base64
import collections
import functools
import json
import logging
from typing import Optional, List

import cryptography.fernet
import flask
import flask_socketio
import peewee
import socketio
from flask_discord import DiscordOAuth2Session
from requests_oauthlib import OAuth2Session

import randovania
from randovania.bitpacking import bitpacking
from randovania.game_description import data_reader
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime import patcher_file
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.game_patches_serializer import BitPackPickupEntry
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.preset import Preset
from randovania.network_common.admin_actions import SessionAdminUserAction, SessionAdminGlobalAction
from randovania.network_common.error import NotLoggedIn, BaseNetworkError, WrongPassword, NotAuthorizedForAction, \
    InvalidSession, InvalidAction, ServerError
from randovania.server.database import User, GameSession, GameSessionPreset, GameSessionMembership, \
    GameSessionTeamAction

fernet_encrypt = cryptography.fernet.Fernet(b'doCWpQK1NhGTC8HBfVIVAa1fqkaOCipT7z6kYJcOgjI=')

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

configuration = randovania.get_configuration()
app.config["DISCORD_CLIENT_ID"] = configuration["discord_client_id"]
app.config["DISCORD_CLIENT_SECRET"] = configuration["discord_client_secret"]
app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback/"  # Redirect URI.
discord = DiscordOAuth2Session(app)

sio = flask_socketio.SocketIO(app)


def _get_server() -> socketio.Server:
    return sio.server


def _get_sio_session(namespace=None):
    return _get_server().get_session(flask.request.sid, namespace=namespace)


def _sio_session(namespace=None):
    return _get_server().session(flask.request.sid, namespace=namespace)


def get_user_with_id(user_id: id) -> User:
    return User.get_by_id(user_id)


def find_user_by_discord_id(discord_id: int) -> Optional[User]:
    try:
        return User.select().where(User.discord_id == discord_id).get()
    except peewee.DoesNotExist:
        return None


def get_current_user() -> User:
    try:
        return get_user_with_id(_get_sio_session()["user-id"])
    except KeyError:
        raise NotLoggedIn()


def exception_on(message, namespace=None):
    def decorator(handler):
        @functools.wraps(handler)
        def _handler(*args):
            try:
                return {
                    "result": handler(*args),
                }
            except BaseNetworkError as error:
                return error.as_json

            except Exception:
                app.logger.exception("Unexpected exception while processing request")
                return ServerError().as_json

        return sio.on(message, namespace)(_handler)

    return decorator


@exception_on("list_game_sessions")
def list_game_sessions():
    return [
        session.create_list_entry()
        for session in GameSession.select()
    ]


def _join_session_via_sio(membership: GameSessionMembership):
    flask_socketio.join_room(f"game-session-{membership.session.id}")
    flask_socketio.join_room(f"game-session-{membership.session.id}-{membership.user.id}")
    with _sio_session() as sio_session:
        sio_session["current_game_session"] = membership.session.id


@exception_on("create_game_session")
def create_game_session(session_name: str):
    with database.db.atomic():
        new_session = GameSession.create(
            name=session_name,
            password=None,
            num_teams=1,
        )
        GameSessionPreset.create(session=new_session, row=0,
                                 preset=json.dumps(PresetManager(None).default_preset.as_json))
        membership = GameSessionMembership.create(
            user=get_current_user(), session=new_session,
            row=0, team=0, admin=True)

    _join_session_via_sio(membership)
    return new_session.create_session_entry()


@exception_on("join_game_session")
def join_game_session(session_id: str, password: Optional[str]):
    session = GameSession.get_by_id(session_id)
    if password != session.password:
        raise WrongPassword()

    membership = GameSessionMembership.get_or_create(user=get_current_user(), session=session,
                                                     defaults={"row": 0, "team": None, "admin": False})[0]

    _emit_session_update(session)
    _join_session_via_sio(membership)

    return session.create_session_entry()


def _verify_has_admin(session_id: int, admin_user_id: Optional[int], *, allow_when_no_admins: bool = False) -> None:
    """
    Checks if the logged user can do admin operations to the given session,
    :param session_id: The GameSessions id
    :param admin_user_id: An user id that is exceptionally authorized for this
    :param allow_when_no_admins: This action is authorized for non-admins if there are no admins.
    :return:
    """
    current_user = get_current_user()
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


@exception_on("game_session_admin_session")
def game_session_admin_session(session_id: int, action: str, arg):
    _verify_has_admin(session_id, None)
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


@exception_on("game_session_admin_player")
def game_session_admin_player(session_id: int, user_id: int, action: str, arg):
    _verify_has_admin(session_id, user_id)
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
        _verify_has_admin(session_id, None, allow_when_no_admins=True)
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


@exception_on("game_session_collect_pickup")
def game_session_collect_pickup(session_id: int, pickup_location: int):
    current_user = get_current_user()
    session: GameSession = database.GameSession.get_by_id(session_id)
    membership = GameSessionMembership.get_by_ids(current_user.id, session_id)

    player_row: int = membership.row

    description = session.layout_description
    pickup_target = description.all_patches[player_row].pickup_assignment.get(PickupIndex(pickup_location))

    if pickup_target is None:
        app.logger.info(f"Session {session_id}, Team {membership.team}, Row {membership.row} found item "
                        f"at {pickup_location}. It's an ETM.")
        return

    preset: Preset = description.permalink.get_preset(pickup_target.player)
    game = data_reader.decode_data(preset.layout_configuration.game_data)

    if pickup_target.player == membership.row:
        app.logger.info(f"Session {session_id}, Team {membership.team}, Row {membership.row} found item "
                        f"at {pickup_location}. It's a {pickup_target.pickup.name} for themselves.")
        encoded_pickup = bitpacking.pack_value(BitPackPickupEntry(pickup_target.pickup, game.resource_database))
        return base64.b85encode(encoded_pickup).decode("utf-8")

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
        app.logger.info(f"Session {session_id}, Team {membership.team}, Row {membership.row} found item "
                        f"at {pickup_location}. It's a {pickup_target.pickup.name} for {pickup_target.player}, "
                        f"but it was already collected.")
        return

    app.logger.info(f"Session {session_id}, Team {membership.team}, Row {membership.row} found item "
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


@exception_on("game_session_request_pickups")
def game_session_request_pickups(session_id: int):
    current_user = get_current_user()
    your_membership = GameSessionMembership.get_by_ids(current_user.id, session_id)
    session: GameSession = your_membership.session

    if not session.in_game:
        app.logger.info(f"Session {session_id}, Team {your_membership.team}, Row {your_membership.row} "
                        f"requested pickups, but session is not in-game.")
        return []

    description = session.layout_description
    row_to_member_name = {
        member.row: member.effective_name
        for member in GameSessionMembership.members_for_team(session, your_membership.team)
    }

    game = data_reader.decode_data(description.permalink.get_preset(your_membership.row).layout_configuration.game_data)

    result = []
    actions: List[GameSessionTeamAction] = list(_query_for_actions(your_membership))
    for action in actions:
        pickup_assignment = description.all_patches[action.provider_row].pickup_assignment
        pickup_target = pickup_assignment.get(PickupIndex(action.provider_location_index))

        if pickup_target is None:
            logging.error(f"Action {action} has a location index with nothing.")
            result.append(None)
        else:
            name = row_to_member_name.get(action.provider_row, f"Player {action.provider_row + 1}")
            result.append({
                "message": f"Received {pickup_target.pickup.name} from {name}",
                "pickup": base64.b85encode(bitpacking.pack_value(
                    BitPackPickupEntry(pickup_target.pickup, game.resource_database)))
            })

    app.logger.info(f"Session {session_id}, Team {your_membership.team}, Row {your_membership.row} "
                    f"requested pickups, returning {len(result)} elements.")

    return result


def _create_client_side_session(user: Optional[database.User] = None):
    """

    :param user: If the session's user was already retrieved, pass it along to avoid an extra query.
    :return:
    """
    session = _get_sio_session()
    encrypted_session = fernet_encrypt.encrypt(json.dumps(session).encode("utf-8"))
    if user is None:
        user = get_user_with_id(session["user-id"])
    elif user.id != session["user-id"]:
        raise RuntimeError(f"Provided user does not match the session's user")

    return {
        "user": user.as_json,
        "sessions": [
            membership.session.create_list_entry()
            for membership in GameSessionMembership.select().where(GameSessionMembership.user == user)
        ],
        "encoded_session_b85": base64.b85encode(encrypted_session),
    }


@exception_on("login_with_discord")
def login_with_discord(code: str):
    oauth = OAuth2Session(
        client_id=app.config["DISCORD_CLIENT_ID"],
        scope=["identify"],
        redirect_uri=app.config["DISCORD_REDIRECT_URI"],
    )
    access_token = oauth.fetch_token(
        "https://discord.com/api/oauth2/token",
        code=code,
        client_secret=app.config["DISCORD_CLIENT_SECRET"],
    )

    flask.session["DISCORD_OAUTH2_TOKEN"] = access_token
    discord_user = discord.fetch_user()

    user: User = User.get_or_create(discord_id=discord_user.id,
                                    defaults={"name": discord_user.name})[0]

    with _sio_session() as session:
        session["user-id"] = user.id
        session["discord-access-token"] = access_token

    return _create_client_side_session(user)


@exception_on("login_with_guest")
def login_with_guest():
    user: User = User.create(name="Guest")

    with _sio_session() as session:
        session["user-id"] = user.id

    return _create_client_side_session(user)


@exception_on("restore_user_session")
def restore_user_session(encrypted_session: bytes, session_id: Optional[int]):
    try:
        decrypted_session: bytes = fernet_encrypt.decrypt(encrypted_session)
        session = json.loads(decrypted_session.decode("utf-8"))

        user = get_user_with_id(session["user-id"])

        if "discord-access-token" in session:
            # TODO: test if the discord access token is still valid
            flask.session["DISCORD_OAUTH2_TOKEN"] = session["discord-access-token"]
        _get_server().save_session(flask.request.sid, session)

        if session_id is not None:
            _join_session_via_sio(GameSessionMembership.get_by_ids(user.id, session_id))

        return _create_client_side_session(user)

    except (KeyError, peewee.DoesNotExist, json.JSONDecodeError):
        raise InvalidSession()

    except Exception:
        logging.exception("Error decoding user session")
        raise InvalidSession()


@app.route("/")
def index():
    return "ok"


if __name__ == '__main__':
    sio.run(app)
