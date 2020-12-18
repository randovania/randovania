import base64
import datetime
import json
from typing import Optional

import cryptography.fernet
import flask
import flask_socketio
import peewee
from requests_oauthlib import OAuth2Session

from randovania.network_common.error import InvalidSession, NotAuthorizedForAction, InvalidAction
from randovania.server.database import User, GameSessionMembership
from randovania.server.lib import logger
from randovania.server.server_app import ServerApp


def _create_client_side_session(sio: ServerApp, user: Optional[User]):
    """

    :param user: If the session's user was already retrieved, pass it along to avoid an extra query.
    :return:
    """
    session = sio.get_session()
    encrypted_session = sio.fernet_encrypt.encrypt(json.dumps(session).encode("utf-8"))
    if user is None:
        user = User.get_by_id(session["user-id"])
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


def login_with_discord(sio: ServerApp, code: str):
    oauth = OAuth2Session(
        client_id=sio.app.config["DISCORD_CLIENT_ID"],
        scope=["identify"],
        redirect_uri=sio.app.config["DISCORD_REDIRECT_URI"],
    )
    access_token = oauth.fetch_token(
        "https://discord.com/api/oauth2/token",
        code=code,
        client_secret=sio.app.config["DISCORD_CLIENT_SECRET"],
    )

    flask.session["DISCORD_OAUTH2_TOKEN"] = access_token
    discord_user = sio.discord.fetch_user()

    user: User = User.get_or_create(discord_id=discord_user.id,
                                    defaults={"name": discord_user.name})[0]
    if user.name != discord_user.name:
        user.name = discord_user.name
        user.save()

    with sio.session() as session:
        session["user-id"] = user.id
        session["discord-access-token"] = access_token

    return _create_client_side_session(sio, user)


def _get_now():
    # For mocking in tests
    return datetime.datetime.now(datetime.timezone.utc)


def login_with_guest(sio: ServerApp, encrypted_login_request: bytes):
    if sio.guest_encrypt is None:
        raise NotAuthorizedForAction()

    try:
        login_request_bytes = sio.guest_encrypt.decrypt(encrypted_login_request)
    except cryptography.fernet.InvalidToken:
        raise NotAuthorizedForAction()

    try:
        login_request = json.loads(login_request_bytes.decode("utf-8"))
        name = login_request["name"]
        date = datetime.datetime.fromisoformat(login_request["date"])
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, ValueError) as e:
        raise InvalidAction(str(e))

    if _get_now() - date > datetime.timedelta(days=1):
        raise NotAuthorizedForAction()

    user: User = User.create(name=f"Guest: {name}")

    with sio.session() as session:
        session["user-id"] = user.id

    return _create_client_side_session(sio, user)


def restore_user_session(sio: ServerApp, encrypted_session: bytes, session_id: Optional[int]):
    try:
        decrypted_session: bytes = sio.fernet_encrypt.decrypt(encrypted_session)
        session = json.loads(decrypted_session.decode("utf-8"))

        user = User.get_by_id(session["user-id"])

        if "discord-access-token" in session:
            # TODO: test if the discord access token is still valid
            flask.session["DISCORD_OAUTH2_TOKEN"] = session["discord-access-token"]
        sio.get_server().save_session(flask.request.sid, session)

        if session_id is not None:
            sio.join_game_session(GameSessionMembership.get_by_ids(user.id, session_id))

        return _create_client_side_session(sio, user)

    except (KeyError, peewee.DoesNotExist, json.JSONDecodeError):
        raise InvalidSession()

    except Exception:
        logger().exception("Error decoding user session")
        raise InvalidSession()


def _emit_user_session_update(sio: ServerApp):
    flask_socketio.emit("user_session_update", _create_client_side_session(sio, None), room=None)


def logout(sio: ServerApp):
    sio.leave_game_session()
    flask.session.pop("DISCORD_OAUTH2_TOKEN", None)
    with sio.session() as session:
        session.pop("discord-access-token", None)
        session.pop("user-id", None)


def setup_app(sio: ServerApp):
    sio.on("login_with_discord", login_with_discord)
    sio.on("login_with_guest", login_with_guest)
    sio.on("restore_user_session", restore_user_session)
    sio.on("logout", logout)
