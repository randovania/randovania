import base64
import datetime
import json

import cryptography.fernet
import flask
import flask_discord.models
import flask_socketio
import oauthlib
import peewee
from oauthlib.oauth2.rfc6749.errors import InvalidTokenError

from randovania.network_common import error
from randovania.server.database import User, UserAccessToken, MultiplayerMembership
from randovania.server.lib import logger
from randovania.server.multiplayer import session_common
from randovania.server.server_app import ServerApp


def _encrypt_session_for_user(sio: ServerApp, session: dict) -> bytes:
    encrypted_session = sio.fernet_encrypt.encrypt(json.dumps(session).encode("utf-8"))
    return base64.b85encode(encrypted_session)


def _create_client_side_session_raw(sio: ServerApp, user: User) -> dict:
    logger().info(f"Client at {sio.current_client_ip()} is user {user.name} ({user.id}).")

    memberships: list[MultiplayerMembership] = list(
        MultiplayerMembership.select().where(MultiplayerMembership.user == user)
    )

    return {
        "user": user.as_json,
        "sessions": [
            membership.session.create_list_entry(user).as_json
            for membership in memberships
        ],
    }


def _create_client_side_session(sio: ServerApp, user: User | None, session: dict | None = None) -> dict:
    """

    :param user: If the session's user was already retrieved, pass it along to avoid an extra query.
    :return:
    """
    if session is None:
        session = sio.get_session()

    if user is None:
        user = User.get_by_id(session["user-id"])
    elif user.id != session["user-id"]:
        raise RuntimeError("Provided user does not match the session's user")

    result = _create_client_side_session_raw(sio, user)
    result["encoded_session_b85"] = _encrypt_session_for_user(sio, session)

    return result


def _create_user_from_discord(discord_user: flask_discord.models.User) -> User:
    fields = discord_user.to_json()

    discord_name = fields.get("global_name")
    if discord_name is None:
        discord_name = discord_user.name

    user: User = User.get_or_create(discord_id=discord_user.id,
                                    defaults={"name": discord_name})[0]
    if user.name != discord_name:
        user.name = discord_name
        user.save()

    return user


def _create_session_with_access_token(sio: ServerApp, token: UserAccessToken) -> bytes:
    return _encrypt_session_for_user(
        sio,
        {
            "user-id": token.user.id,
            "rdv-access-token": token.name,
        }
    )


def _create_session_with_discord_token(sio: ServerApp, sid: str | None) -> User:
    discord_user = sio.discord.fetch_user()

    if sio.enforce_role is not None:
        if not sio.enforce_role.verify_user(discord_user.id):
            logger().info("User %s is not authorized for connecting to the server", discord_user.name)
            raise error.UserNotAuthorizedToUseServerError()

    user = _create_user_from_discord(discord_user)

    if sid is None:
        return user

    with sio.session(sid=sid) as session:
        session["user-id"] = user.id
        session["discord-access-token"] = flask.session["DISCORD_OAUTH2_TOKEN"]

    return user


def start_discord_login_flow(sio: ServerApp):
    return flask.request.sid


def _get_now():
    # For mocking in tests
    return datetime.datetime.now(datetime.timezone.utc)


def login_with_guest(sio: ServerApp, encrypted_login_request: bytes):
    if sio.guest_encrypt is None:
        raise error.NotAuthorizedForActionError()

    try:
        login_request_bytes = sio.guest_encrypt.decrypt(encrypted_login_request)
    except cryptography.fernet.InvalidToken:
        raise error.NotAuthorizedForActionError()

    try:
        login_request = json.loads(login_request_bytes.decode("utf-8"))
        name = login_request["name"]
        date = datetime.datetime.fromisoformat(login_request["date"])
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, ValueError) as e:
        raise error.InvalidActionError(str(e))

    if _get_now() - date > datetime.timedelta(days=1):
        raise error.NotAuthorizedForActionError()

    user: User = User.create(name=f"Guest: {name}")

    with sio.session() as session:
        session["user-id"] = user.id

    return _create_client_side_session(sio, user)


def restore_user_session(sio: ServerApp, encrypted_session: bytes, _old_session_id: None = None):
    # _old_session_id exists to keep compatibility with old dev build clients that try to connect
    try:
        decrypted_session: bytes = sio.fernet_encrypt.decrypt(encrypted_session)
        session = json.loads(decrypted_session.decode("utf-8"))

        if "discord-access-token" in session:
            flask.session["DISCORD_OAUTH2_TOKEN"] = session["discord-access-token"]
            user = _create_session_with_discord_token(sio, sio.request_sid)
            result = _create_client_side_session(sio, user)
        else:
            user = User.get_by_id(session["user-id"])
            sio.save_session(session)

            if "rdv-access-token" in session:
                access_token = UserAccessToken.get(
                    user=user,
                    name=session["rdv-access-token"],
                )
                access_token.last_used = datetime.datetime.now(datetime.timezone.utc)
                access_token.save()

                result = _create_client_side_session_raw(sio, user)

            else:
                result = _create_client_side_session(sio, user)

        return result

    except error.UserNotAuthorizedToUseServerError:
        sio.save_session({})
        raise

    except (KeyError, peewee.DoesNotExist, json.JSONDecodeError, InvalidTokenError) as e:
        # InvalidTokenError: discord token expired and couldn't renew
        sio.save_session({})
        logger().info("Client at %s was unable to restore session: (%s) %s",
                      sio.current_client_ip(), str(type(e)), str(e))
        raise error.InvalidSessionError()

    except Exception:
        sio.save_session({})
        logger().exception("Error decoding user session")
        raise error.InvalidSessionError()


def logout(sio: ServerApp):
    session_common.leave_all_rooms(sio)
    flask.session.pop("DISCORD_OAUTH2_TOKEN", None)
    with sio.session() as session:
        session.pop("discord-access-token", None)
        session.pop("user-id", None)


def browser_login_with_discord(sio: ServerApp):
    sid = flask.request.args.get('sid')
    if sid is not None:
        if not sio.get_server().rooms(sid):
            return flask.render_template(
                "unable_to_login.html",
                error_message="Invalid sid received from Randovania!",
            ), 400

        flask.session["sid"] = sid
    else:
        flask.session.pop("sid", None)

    return sio.discord.create_session()


def browser_discord_login_callback(sio: ServerApp):
    try:
        sio.discord.callback()

        sid = flask.session.get("sid")
        user = _create_session_with_discord_token(sio, sid)

        if sid is None:
            return flask.redirect(flask.url_for("browser_me"))
        else:
            try:
                session = sio.get_session(sid=sid)
            except KeyError:
                return flask.render_template(
                    "unable_to_login.html",
                    error_message="Unable to find your Randovania client.",
                ), 401

            result = _create_client_side_session(sio, user, session)
            flask_socketio.emit("user_session_update", result, to=sid, namespace="/")
            return flask.render_template(
                "return_to_randovania.html",
                user=user,
            )

    except flask_discord.exceptions.AccessDenied:
        return flask.render_template(
            "unable_to_login.html",
            error_message="Discord login was cancelled. Please try again!",
        ), 401

    except error.UserNotAuthorizedToUseServerError:
        return flask.render_template(
            "unable_to_login.html",
            error_message="You're not authorized to use this build.\nPlease check #dev-builds for more details.",
        ), 403

    except oauthlib.oauth2.rfc6749.errors.OAuth2Error as err:
        if isinstance(err, oauthlib.oauth2.rfc6749.errors.InvalidGrantError):
            logger().info("Invalid grant when finishing Discord login")
        else:
            logger().exception("OAuth2Error when finishing Discord login")

        return flask.render_template(
            "unable_to_login.html",
            error_message=f"Unable to complete login. Please try again! {err}",
        ), 500


def setup_app(sio: ServerApp):
    sio.on("start_discord_login_flow", start_discord_login_flow)
    sio.on("login_with_guest", login_with_guest)
    sio.on("restore_user_session", restore_user_session)
    sio.on("logout", logout)

    sio.route_path("/login", browser_login_with_discord)
    sio.route_path("/login_callback", browser_discord_login_callback)

    @sio.route_with_user("/me")
    def browser_me(user: User):
        result = f"Hello {user.name}. Admin? {user.admin}<br />Access Tokens:<ul>\n"

        for token in user.access_tokens:
            delete = f' <a href="{flask.url_for("delete_token", token=token.name)}">Delete</a>'
            result += (f"<li>{token.name} created at {token.creation_date}."
                       f" Last used at {token.last_used}. {delete}</li>")

        result += f'<li><form class="form-inline" method="POST" action="{flask.url_for("create_token")}">'
        result += '<input id="name" placeholder="Access token name" name="name">'
        result += '<button type="submit">Create new</button></li></ul>'

        return result

    @sio.route_with_user("/create_token", methods=["POST"])
    def create_token(user: User):
        token_name: str = flask.request.form['name']
        go_back = f'<a href="{flask.url_for("browser_me")}">Go back</a>'

        try:
            token = UserAccessToken.create(
                user=user,
                name=token_name,
            )
            session = _create_session_with_access_token(sio, token).decode("ascii")
            return f'Token: <pre>{session}</pre><br />{go_back}'

        except peewee.IntegrityError as e:
            return f'Unable to create token: {e}<br />{go_back}'

    @sio.route_with_user("/delete_token")
    def delete_token(user: User):
        token_name: str = flask.request.args['token']
        UserAccessToken.get(
            user=user,
            name=token_name,
        ).delete_instance()
        return flask.redirect(flask.url_for("browser_me"))
