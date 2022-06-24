import datetime
import functools
import json
from pathlib import Path

import pypresence
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

import randovania
from randovania.gui.lib import async_dialog
from randovania.network_client.game_session import GameSessionEntry, User, GameSessionActions, GameSessionPickups, \
    GameSessionAuditLog
from randovania.network_client.network_client import NetworkClient, ConnectionState, UnableToConnect
from randovania.network_common.error import (InvalidAction, NotAuthorizedForAction, ServerError, RequestTimeout,
                                             NotLoggedIn, UserNotAuthorized, UnsupportedClient)


class QtNetworkClient(QWidget, NetworkClient):
    Connect = Signal()
    ConnectError = Signal()
    Disconnect = Signal()
    UserChanged = Signal(User)
    ConnectionStateUpdated = Signal(ConnectionState)
    GameSessionMetaUpdated = Signal(GameSessionEntry)
    GameSessionActionsUpdated = Signal(GameSessionActions)
    GameSessionPickupsUpdated = Signal(GameSessionPickups)
    GameSessionAuditLogUpdated = Signal(GameSessionAuditLog)
    GameUpdateNotification = Signal()

    discord: pypresence.AioClient | None = None

    def __init__(self, user_data_dir: Path):
        super().__init__()
        NetworkClient.__init__(self, user_data_dir.joinpath("network_client"), randovania.get_configuration())
        from randovania.gui.lib import common_qt_lib
        common_qt_lib.set_default_window_icon(self)

    @NetworkClient.connection_state.setter
    def connection_state(self, value: ConnectionState):
        NetworkClient.connection_state.fset(self, value)
        self.ConnectionStateUpdated.emit(value)

    async def on_connect(self):
        await super().on_connect()
        self.Connect.emit()

    async def on_connect_error(self, error_message: str):
        await super().on_connect_error(error_message)
        self.ConnectError.emit()

    async def on_disconnect(self):
        await super().on_disconnect()
        self.Disconnect.emit()

    async def on_user_session_updated(self, new_session: dict):
        await super().on_user_session_updated(new_session)
        self.UserChanged.emit(self.current_user)

    async def on_game_session_meta_update(self, entry: GameSessionEntry):
        await super().on_game_session_meta_update(entry)
        self.GameSessionMetaUpdated.emit(entry)

    async def on_game_session_actions_update(self, actions: GameSessionActions):
        await super().on_game_session_actions_update(actions)
        self.GameSessionActionsUpdated.emit(actions)

    async def on_game_session_pickups_update(self, pickups: GameSessionPickups):
        await super().on_game_session_pickups_update(pickups)
        self.GameSessionPickupsUpdated.emit(pickups)

    async def on_game_session_audit_update(self, audit_log: GameSessionAuditLog):
        await super().on_game_session_audit_update(audit_log)
        self.GameSessionAuditLogUpdated.emit(audit_log)

    async def login_with_discord(self):
        if "discord_client_id" not in self.configuration:
            raise RuntimeError("Missing Discord configuration for Randovania")

        self.discord = pypresence.AioClient(self.configuration["discord_client_id"])
        self.discord._events_on = False  # workaround for broken AioClient
        await self.discord.start()

        authorize = await self.discord.authorize(self.configuration["discord_client_id"], ['identify'])

        new_session = await self._emit_with_result("login_with_discord", authorize["data"]["code"])
        await self.on_user_session_updated(new_session)

    async def login_as_guest(self, name: str = "Unknown"):
        if "guest_secret" not in self.configuration:
            raise RuntimeError("Missing guest configuration for Randovania")

        from cryptography.fernet import Fernet
        fernet = Fernet(self.configuration["guest_secret"].encode("ascii"))
        login_request = fernet.encrypt(json.dumps({
            "name": name,
            "date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }).encode("utf-8"))

        new_session = await self._emit_with_result("login_with_guest", login_request)
        await self.on_user_session_updated(new_session)

    async def on_game_update_notification(self, details):
        self.GameUpdateNotification.emit()

    @property
    def available_login_methods(self) -> set[str]:
        methods = []
        if "guest_secret" in self.configuration:
            methods.append("guest")
        if "discord_client_id" in self.configuration:
            methods.append("discord")
        return set(methods)


def handle_network_errors(fn):
    @functools.wraps(fn)
    async def wrapper(self, *args, **kwargs):
        try:
            return await fn(self, *args, **kwargs)

        except InvalidAction as e:
            await async_dialog.warning(self, "Invalid action", f"{e}")

        except ServerError:
            await async_dialog.warning(self, "Server error",
                                       "An error occurred on the server while processing your request.")

        except NotLoggedIn:
            await async_dialog.warning(self, "Unauthenticated",
                                       "You must be logged in.")

        except NotAuthorizedForAction:
            await async_dialog.warning(self, "Unauthorized",
                                       "You're not authorized to perform that action.")

        except UserNotAuthorized:
            await async_dialog.warning(
                self, "Unauthorized",
                "You're not authorized to use this build.\nPlease check #dev-builds for more details.",
            )

        except UnsupportedClient as e:
            s = e.detail.replace('\n', '<br />')
            await async_dialog.warning(
                self, "Unsupported client",
                s,
            )

        except UnableToConnect as e:
            s = e.reason.replace('\n', '<br />')
            await async_dialog.warning(self, "Connection Error",
                                       f"<b>Unable to connect to the server:</b><br /><br />{s}")

        except RequestTimeout as e:
            await async_dialog.warning(self, "Connection Error",
                                       f"<b>Timeout while communicating with the server:</b><br /><br />{e}"
                                       f"<br />Further attempts will wait for longer.")

        return None

    return wrapper
