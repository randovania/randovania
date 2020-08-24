import base64
import json
from typing import Optional

import cryptography.fernet
import flask
import peewee
from flask_discord import DiscordOAuth2Session
from requests_oauthlib import OAuth2Session

from randovania.network_common.error import InvalidSession
from randovania.server.database import User, GameSessionMembership
from randovania.server.lib import logger
from randovania.server.socket_wrapper import SocketWrapper


def setup_app(app: flask.Flask, sio: SocketWrapper):
    discord = DiscordOAuth2Session(app)
    fernet_encrypt = cryptography.fernet.Fernet(b'doCWpQK1NhGTC8HBfVIVAa1fqkaOCipT7z6kYJcOgjI=')

    def _create_client_side_session(user: Optional[User] = None):
        """

        :param user: If the session's user was already retrieved, pass it along to avoid an extra query.
        :return:
        """
        session = sio.get_session()
        encrypted_session = fernet_encrypt.encrypt(json.dumps(session).encode("utf-8"))
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

    @sio.exception_on("login_with_discord")
    def login_with_discord(code: str):
        oauth = OAuth2Session(
            client_id=flask.current_app.config["DISCORD_CLIENT_ID"],
            scope=["identify"],
            redirect_uri=flask.current_app.config["DISCORD_REDIRECT_URI"],
        )
        access_token = oauth.fetch_token(
            "https://discord.com/api/oauth2/token",
            code=code,
            client_secret=flask.current_app.config["DISCORD_CLIENT_SECRET"],
        )

        flask.session["DISCORD_OAUTH2_TOKEN"] = access_token
        discord_user = discord.fetch_user()

        user: User = User.get_or_create(discord_id=discord_user.id,
                                        defaults={"name": discord_user.name})[0]

        with sio.session() as session:
            session["user-id"] = user.id
            session["discord-access-token"] = access_token

        return _create_client_side_session(user)

    @sio.exception_on("login_with_guest")
    def login_with_guest():
        user: User = User.create(name="Guest")

        with sio.session() as session:
            session["user-id"] = user.id

        return _create_client_side_session(user)

    @sio.exception_on("restore_user_session")
    def restore_user_session(encrypted_session: bytes, session_id: Optional[int]):
        try:
            decrypted_session: bytes = fernet_encrypt.decrypt(encrypted_session)
            session = json.loads(decrypted_session.decode("utf-8"))

            user = User.get_by_id(session["user-id"])

            if "discord-access-token" in session:
                # TODO: test if the discord access token is still valid
                flask.session["DISCORD_OAUTH2_TOKEN"] = session["discord-access-token"]
            sio.get_server().save_session(flask.request.sid, session)

            if session_id is not None:
                sio.join_session_via_sio(GameSessionMembership.get_by_ids(user.id, session_id))

            return _create_client_side_session(user)

        except (KeyError, peewee.DoesNotExist, json.JSONDecodeError):
            raise InvalidSession()

        except Exception:
            logger().exception("Error decoding user session")
            raise InvalidSession()
