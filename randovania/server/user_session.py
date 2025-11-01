from __future__ import annotations

import base64
import datetime
import json
import typing

import cryptography.fernet
import jwt
import oauthlib
import peewee
from fastapi import APIRouter, Form, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from oauthlib.common import generate_token
from oauthlib.oauth2.rfc6749.errors import raise_from_error
from pydantic import BaseModel, model_validator

from randovania.network_common import error as network_error
from randovania.server import fastapi_discord
from randovania.server.database import User, UserAccessToken
from randovania.server.multiplayer import session_common
from randovania.server.server_app import ServerAppDep, UserDep

if typing.TYPE_CHECKING:
    from randovania.server.fastapi_discord import DiscordUser
    from randovania.server.server_app import ServerApp


router = APIRouter()


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


def _create_user_from_discord(discord_user: DiscordUser) -> User:
    discord_name = discord_user.global_name

    if discord_name is None:
        discord_name = discord_user.username

    user, created = User.get_or_create(discord_id=int(discord_user.id), defaults={"name": discord_name})

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


async def _create_session_with_discord_token(sa: ServerApp, sid: str | None, token: str) -> User:
    discord_user = await sa.discord.user(token)

    if sa.enforce_role is not None:
        if not await sa.enforce_role.verify_user(discord_user.id):
            sa.logger.info("User %s is not authorized for connecting to the server", discord_user.username)
            raise network_error.UserNotAuthorizedToUseServerError(discord_user.username)

    user = _create_user_from_discord(discord_user)

    if sid is None:
        return user

    async with sa.sio.session(sid=sid) as session:
        session["user-id"] = user.id
        session["discord-access-token"] = token

    return user


async def start_discord_login_flow(sa: ServerApp, sid: str) -> str:
    return sid


def _get_now() -> datetime.datetime:
    # For mocking in tests
    return datetime.datetime.now(datetime.UTC)


async def login_with_guest(sa: ServerApp, sid: str, encrypted_login_request: bytes) -> dict:
    if sa.guest_encrypt is None:
        raise network_error.NotAuthorizedForActionError

    try:
        login_request_bytes = sa.guest_encrypt.decrypt(encrypted_login_request)
    except cryptography.fernet.InvalidToken:
        raise network_error.NotAuthorizedForActionError

    try:
        login_request = json.loads(login_request_bytes.decode("utf-8"))
        name = login_request["name"]
        date = datetime.datetime.fromisoformat(login_request["date"])
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, ValueError) as e:
        raise network_error.InvalidActionError(str(e))

    if _get_now() - date > datetime.timedelta(days=1):
        raise network_error.NotAuthorizedForActionError

    user: User = User.create(name=f"Guest: {name}")

    async with sa.sio.session(sid) as session:
        session["user-id"] = user.id

    return await _create_client_side_session(sa, sid, user)


async def restore_user_session(sa: ServerApp, sid: str, encrypted_session: bytes, _old_session_id: None = None) -> dict:
    # _old_session_id exists to keep compatibility with old dev build clients that try to connect
    try:
        decrypted_session: bytes = sa.fernet_encrypt.decrypt(encrypted_session)
        session = json.loads(decrypted_session.decode("utf-8"))

        if "discord-access-token" in session:
            user = await _create_session_with_discord_token(sa, sid, session["discord-access-token"])
            result = await _create_client_side_session(sa, sid, user)
        else:
            user = User.get_by_id(session["user-id"])
            await sa.sio.save_session(sid, session)

            if "rdv-access-token" in session:
                access_token = UserAccessToken.get(
                    user=user,
                    name=session["rdv-access-token"],
                )
                access_token.last_used = datetime.datetime.now(datetime.UTC)
                access_token.save()

                result = _create_client_side_session_raw(sa, sid, user)

            else:
                result = await _create_client_side_session(sa, sid, user)

        return result

    except network_error.UserNotAuthorizedToUseServerError:
        await sa.sio.save_session(sid, {})
        raise

    except (KeyError, peewee.DoesNotExist, json.JSONDecodeError, fastapi_discord.exceptions.Unauthorized) as e:
        # Unauthorized: bad discord access token. Expired?
        await sa.sio.save_session(sid, {})
        sa.logger.info(
            "Client at %s was unable to restore session: (%s) %s", sa.current_client_ip(sid), str(type(e)), str(e)
        )
        raise network_error.InvalidSessionError

    except Exception:
        await sa.sio.save_session(sid, {})
        sa.logger.exception("Error decoding user session")
        raise network_error.InvalidSessionError


async def logout(sa: ServerApp, sid: str) -> None:
    await session_common.leave_all_rooms(sa, sid)
    async with sa.sio.session(sid) as session:
        session.pop("discord-access-token", None)
        session.pop("user-id", None)


def unable_to_login(sa: ServerApp, request: Request, error_message: str, status_code: int) -> HTMLResponse:
    return sa.templates.TemplateResponse(
        request=request,
        name="user_session/unable_to_login.html.jinja",
        context={
            "error_message": error_message,
        },
        status_code=status_code,
    )


@router.get("/login")
async def browser_login_with_discord(sa: ServerAppDep, request: Request, sid: str | None = None) -> Response:
    request.state.sid = sid

    state = jwt.encode(
        {"__state_secret": generate_token()},
        sa.configuration["server_config"]["secret_key"],
        algorithm="HS256",
    )
    request.session["discord_oauth_state"] = state

    if sid is not None:
        if not sa.sio.rooms(sid):
            return unable_to_login(sa, request, "Invalid sid received from Randovania!", 400)

        request.session["sid"] = sid
    else:
        request.session.pop("sid", None)

    return RedirectResponse(sa.discord.get_oauth_login_url(request, state))


class DiscordLoginCallbackParams(BaseModel):
    code: str | None = None
    state: str | None = None
    error: str | None = None
    error_description: str | None = None

    @model_validator(mode="after")
    def check_all_provided(self) -> typing.Self:
        if self.error is None:
            if self.code is None:
                raise ValueError("'code' param must be provided")
            if self.state is None:
                raise ValueError("'state' param must be provided")

        return self


@router.get("/login_callback")
async def browser_discord_login_callback(
    sa: ServerAppDep,
    request: Request,
    params: typing.Annotated[DiscordLoginCallbackParams, Query()],
) -> Response:
    code = params.code
    state = params.state
    error = params.error
    error_description = params.error_description

    sid: str | None = request.session.get("sid")

    try:
        if error is not None:
            error_params = {}
            if error_description is not None:
                error_params["error_description"] = error_description
            raise_from_error(error, error_params)

        # code and state are only None when there's an error
        assert code is not None
        assert state is not None

        if state != request.session.get("discord_oauth_state", ""):
            raise oauthlib.oauth2.rfc6749.errors.MismatchingStateError

        token, refresh_token = await sa.discord.get_access_token(code)
        request.session["discord_oauth_token"] = token
        request.session["discord_oauth_refresh_token"] = refresh_token

        user = await _create_session_with_discord_token(sa, sid, token)

        if sid is None:
            return RedirectResponse(request.url_for("browser_me"))
        else:
            try:
                session = await sa.sio.get_session(sid=sid)
            except KeyError:
                return unable_to_login(sa, request, "Unable to find your Randovania client.", 401)

            result = await _create_client_side_session(sa, sid, user, session)
            await sa.sio.emit("user_session_update", result, to=sid, namespace="/")

            return sa.templates.TemplateResponse(
                request,
                "user_session/return_to_randovania.html.jinja",
                context={
                    "user": user,
                },
            )

    except fastapi_discord.exceptions.Unauthorized:
        error_message = "Discord login was cancelled. Please try again!"
        status_code = 401

    except network_error.UserNotAuthorizedToUseServerError as unauthorized_error:
        error_message = (
            f"You ({unauthorized_error.unauthorized_user}) are not authorized to use this build.\n"
            f"Please check #dev-builds for more details."
        )
        status_code = 403

    except (
        oauthlib.oauth2.rfc6749.errors.MismatchingStateError,
        fastapi_discord.exceptions.InvalidToken,
    ):
        error_message = "You must finish the login with the same browser that you started it with."
        status_code = 401

    except oauthlib.oauth2.rfc6749.errors.OAuth2Error as err:
        print(err)
        if isinstance(err, oauthlib.oauth2.rfc6749.errors.InvalidGrantError):
            sa.logger.info("Invalid grant when finishing Discord login")
        else:
            sa.logger.exception("OAuth2Error when finishing Discord login")

        error_message = f"Unable to complete login. Please try again! {err}"
        status_code = 500

    return unable_to_login(sa, request, error_message, status_code)


@router.get("/me", response_class=HTMLResponse)
async def browser_me(sa: ServerAppDep, request: Request, user: UserDep) -> HTMLResponse:
    return sa.templates.TemplateResponse(
        request,
        "user_session/me.html.jinja",
        context={
            "user": user,
            "is_admin": user.admin or sa.app.debug,
        },
    )


@router.post("/create_token", response_class=HTMLResponse)
async def create_token(
    sa: ServerAppDep, request: Request, user: UserDep, name: typing.Annotated[str, Form()]
) -> HTMLResponse:
    try:
        token = UserAccessToken.create(
            user=user,
            name=name,
        )
        session = _create_session_with_access_token(sa, token).decode("ascii")
        context = {
            "created": True,
            "token": session,
        }
        status_code = 200

    except peewee.IntegrityError as e:
        context = {
            "created": False,
            "error": str(e),
        }
        status_code = 500

    return sa.templates.TemplateResponse(
        request=request,
        name="user_session/token_created.html.jinja",
        context=context,
        status_code=status_code,
    )


@router.get("/delete_token")
async def delete_token(request: Request, user: UserDep, token: str) -> RedirectResponse:
    UserAccessToken.get(
        user=user,
        name=token,
    ).delete_instance()
    return RedirectResponse(request.url_for("browser_me"))


def setup_app(sa: ServerApp) -> None:
    sa.on("start_discord_login_flow", start_discord_login_flow)
    sa.on("login_with_guest", login_with_guest)
    sa.on("restore_user_session", restore_user_session)
    sa.on("logout", logout)

    sa.app.include_router(router)
