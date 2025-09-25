from __future__ import annotations

import base64
import datetime
import json
import typing

import cryptography.fernet

# import flask
# import flask_discord.models
# import flask_socketio
import fastapi_discord
import oauthlib
import peewee
from fastapi import Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from oauthlib.oauth2.rfc6749.errors import InvalidTokenError

from randovania.network_common import error
from randovania.server.database import User, UserAccessToken
from randovania.server.multiplayer import session_common
from randovania.server.server_app import ServerAppDep

if typing.TYPE_CHECKING:
    from randovania.server.server_app import ServerApp


def _encrypt_session_for_user(sa: ServerApp, session: dict) -> bytes:
    encrypted_session = sa.fernet_encrypt.encrypt(json.dumps(session).encode("utf-8"))
    return base64.b85encode(encrypted_session)


def _create_client_side_session_raw(sa: ServerApp, sid: str, user: User) -> dict:
    sa.logger.info(f"Client at {sa.current_client_ip(sid)} is user {user.name} ({user.id}).")

    return {
        "user": user.as_json,
    }


async def _create_client_side_session(sa: ServerApp, sid: str, user: User | None, session: dict | None = None) -> dict:
    """

    :param user: If the session's user was already retrieved, pass it along to avoid an extra query.
    :return:
    """
    if session is None:
        session = await sa.sio.get_session(sid)

    if user is None:
        user = User.get_by_id(session["user-id"])
    elif user.id != session["user-id"]:
        raise RuntimeError("Provided user does not match the session's user")

    result = _create_client_side_session_raw(sa, sid, user)
    result["encoded_session_b85"] = _encrypt_session_for_user(sa, session)

    return result


def _create_user_from_discord(discord_user: fastapi_discord.User) -> User:
    discord_name = discord_user.global_name

    if discord_name is None:
        discord_name = discord_user.username

    user: User = User.get_or_create(discord_id=int(discord_user.id), defaults={"name": discord_name})[0]
    if user.name != discord_name:
        user.name = discord_name
        user.save()

    return user


def _create_session_with_access_token(sa: ServerApp, token: UserAccessToken) -> bytes:
    return _encrypt_session_for_user(
        sa,
        {
            "user-id": token.user.id,
            "rdv-access-token": token.name,
        },
    )


async def _create_session_with_discord_token(sa: ServerApp, sid: str | None, request: Request) -> User:
    discord_user = await sa.discord.user(request)

    if sa.enforce_role is not None:
        if not sa.enforce_role.verify_user(discord_user.id):
            sa.logger.info("User %s is not authorized for connecting to the server", discord_user.name)
            raise error.UserNotAuthorizedToUseServerError(discord_user.name)

    sa.logger.info(f"{discord_user.id} ({type(discord_user.id)})")
    user = _create_user_from_discord(discord_user)

    if sid is None:
        return user

    async with sa.sio.session(sid=sid) as session:
        session["user-id"] = user.id
        session["discord-access-token"] = request.session["discord_oauth_token"]

    return user


async def start_discord_login_flow(sa: ServerApp, sid: str):
    return sid


def _get_now():
    # For mocking in tests
    return datetime.datetime.now(datetime.UTC)


async def login_with_guest(sa: ServerApp, encrypted_login_request: bytes):
    if sa.guest_encrypt is None:
        raise error.NotAuthorizedForActionError

    try:
        login_request_bytes = sa.guest_encrypt.decrypt(encrypted_login_request)
    except cryptography.fernet.InvalidToken:
        raise error.NotAuthorizedForActionError

    try:
        login_request = json.loads(login_request_bytes.decode("utf-8"))
        name = login_request["name"]
        date = datetime.datetime.fromisoformat(login_request["date"])
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, ValueError) as e:
        raise error.InvalidActionError(str(e))

    if _get_now() - date > datetime.timedelta(days=1):
        raise error.NotAuthorizedForActionError

    user: User = User.create(name=f"Guest: {name}")

    with sa.sio.session() as session:
        session["user-id"] = user.id

    return _create_client_side_session(sa, user)


async def restore_user_session(sa: ServerApp, encrypted_session: bytes, _old_session_id: None = None):
    # _old_session_id exists to keep compatibility with old dev build clients that try to connect
    try:
        decrypted_session: bytes = sa.fernet_encrypt.decrypt(encrypted_session)
        session = json.loads(decrypted_session.decode("utf-8"))

        if "discord-access-token" in session:
            flask.session["DISCORD_OAUTH2_TOKEN"] = session["discord-access-token"]
            user = _create_session_with_discord_token(sa, sa.request_sid)
            result = _create_client_side_session(sa, user)
        else:
            user = User.get_by_id(session["user-id"])
            sa.sio.save_session(session)

            if "rdv-access-token" in session:
                access_token = UserAccessToken.get(
                    user=user,
                    name=session["rdv-access-token"],
                )
                access_token.last_used = datetime.datetime.now(datetime.UTC)
                access_token.save()

                result = _create_client_side_session_raw(sa, user)

            else:
                result = _create_client_side_session(sa, user)

        return result

    except error.UserNotAuthorizedToUseServerError:
        sa.sio.save_session({})
        raise

    except (KeyError, peewee.DoesNotExist, json.JSONDecodeError, InvalidTokenError) as e:
        # InvalidTokenError: discord token expired and couldn't renew
        sa.sio.save_session({})
        sa.logger.info(
            "Client at %s was unable to restore session: (%s) %s", sa.current_client_ip(), str(type(e)), str(e)
        )
        raise error.InvalidSessionError

    except Exception:
        sa.sio.save_session({})
        sa.logger.exception("Error decoding user session")
        raise error.InvalidSessionError


async def logout(sa: ServerApp):
    session_common.leave_all_rooms(sa)
    flask.session.pop("DISCORD_OAUTH2_TOKEN", None)
    with sa.sio.session() as session:
        session.pop("discord-access-token", None)
        session.pop("user-id", None)


def unable_to_login(sa: ServerApp, request: Request, error_message: str, status_code: int) -> HTMLResponse:
    return sa.templates.TemplateResponse(
        request=request,
        name="unable_to_login.html",
        context={
            "error_message": error_message,
        },
        status_code=status_code,
    )


async def browser_login_with_discord(sa: ServerAppDep, request: Request, sid: str | None = None) -> Response:
    request.state.sid = sid

    if sid is not None:
        if not sa.sio.rooms(sid):
            return unable_to_login(sa, request, "Invalid sid received from Randovania!", 400)

        request.session["sid"] = sid
    else:
        request.session.pop("sid", None)

    return RedirectResponse(sa.discord.get_oauth_login_url())


async def browser_discord_login_callback(
    sa: ServerAppDep,
    request: Request,
    code: str,
) -> Response:
    sid: str | None = request.session.get("sid")

    try:
        token, refresh_token = await sa.discord.get_access_token(code)
        request.headers
        request.session["discord_oauth_token"] = token
        request.session["discord_oauth_refresh_token"] = refresh_token

        user = await _create_session_with_discord_token(sa, sid, request)

        if sid is None:
            return RedirectResponse(request.url_for("/me"))
        else:
            try:
                session = await sa.sio.get_session(sid=sid)
            except KeyError:
                return unable_to_login(sa, request, "Unable to find your Randovania client.", 401)

            result = await _create_client_side_session(sa, sid, user, session)
            await sa.sio.emit("user_session_update", result, to=sid, namespace="/")

            return sa.templates.TemplateResponse(
                request,
                "return_to_randovania.html",
                context={
                    "user": user,
                },
            )

    except fastapi_discord.exceptions.Unauthorized:
        error_message = "Discord login was cancelled. Please try again!"
        status_code = 401

    except error.UserNotAuthorizedToUseServerError as unauthorized_error:
        error_message = (
            f"You ({unauthorized_error.unauthorized_user}) are not authorized to use this build.\n"
            f"Please check #dev-builds for more details."
        )
        status_code = 403

    except oauthlib.oauth2.rfc6749.errors.MismatchingStateError:
        error_message = "You must finish the login with the same browser that you started it with."
        status_code = 401

    except oauthlib.oauth2.rfc6749.errors.OAuth2Error as err:
        if isinstance(err, oauthlib.oauth2.rfc6749.errors.InvalidGrantError):
            sa.logger.info("Invalid grant when finishing Discord login")
        else:
            sa.logger.exception("OAuth2Error when finishing Discord login")

        error_message = f"Unable to complete login. Please try again! {err}"
        status_code = 500

    return unable_to_login(sa, request, error_message, status_code)


def setup_app(sa: ServerApp):
    sa.on("start_discord_login_flow", start_discord_login_flow)
    sa.on("login_with_guest", login_with_guest)
    sa.on("restore_user_session", restore_user_session)
    sa.on("logout", logout)

    sa.app.get("/login")(browser_login_with_discord)
    sa.app.get("/login_callback")(browser_discord_login_callback)

    @sa.route_with_user("/me")
    def browser_me(user: User):
        result = f"Hello {user.name}. Admin? {user.admin}<br />Access Tokens:<ul>\n"

        for token in user.access_tokens:
            delete = f' <a href="{flask.url_for("delete_token", token=token.name)}">Delete</a>'
            result += (
                f"<li>{token.name} created at {token.creation_date}. Last used at {token.last_used}. {delete}</li>"
            )

        result += f'<li><form class="form-inline" method="POST" action="{flask.url_for("create_token")}">'
        result += '<input id="name" placeholder="Access token name" name="name">'
        result += '<button type="submit">Create new</button></li></ul>'

        return result

    @sa.route_with_user("/create_token", methods=["POST"])
    def create_token(user: User):
        token_name: str = flask.request.form["name"]
        go_back = f'<a href="{flask.url_for("browser_me")}">Go back</a>'

        try:
            token = UserAccessToken.create(
                user=user,
                name=token_name,
            )
            session = _create_session_with_access_token(sa, token).decode("ascii")
            return f"Token: <pre>{session}</pre><br />{go_back}"

        except peewee.IntegrityError as e:
            return f"Unable to create token: {e}<br />{go_back}"

    @sa.route_with_user("/delete_token")
    def delete_token(user: User):
        token_name: str = flask.request.args["token"]
        UserAccessToken.get(
            user=user,
            name=token_name,
        ).delete_instance()
        return flask.redirect(flask.url_for("browser_me"))
