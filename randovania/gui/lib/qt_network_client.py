from pathlib import Path
from typing import Optional

import pypresence
from PySide2.QtCore import Signal
from PySide2.QtWidgets import QWidget

import randovania
from randovania.gui.lib import async_dialog
from randovania.network_client.game_session import GameSessionEntry
from randovania.network_client.network_client import NetworkClient, ConnectionState
from randovania.network_common.error import InvalidAction, NotAuthorizedForAction, ServerError


class QtNetworkClient(QWidget, NetworkClient):
    Connect = Signal()
    ConnectError = Signal()
    Disconnect = Signal()
    ConnectionStateUpdated = Signal(ConnectionState)
    GameSessionUpdated = Signal(GameSessionEntry)
    GameUpdateNotification = Signal()

    discord: Optional[pypresence.AioClient]

    def __init__(self, user_data_dir: Path):
        super().__init__()
        NetworkClient.__init__(self, user_data_dir.joinpath("network_client"), randovania.get_configuration())
        from randovania.gui.lib import common_qt_lib
        common_qt_lib.set_default_window_icon(self)

        if "discord_client_id" in self.configuration:
            self.discord = pypresence.AioClient(self.configuration["discord_client_id"])
            self.discord._events_on = False  # workaround for broken AioClient
        else:
            self.discord = None

    @NetworkClient.connection_state.setter
    def connection_state(self, value: ConnectionState):
        NetworkClient.connection_state.fset(self, value)
        self.ConnectionStateUpdated.emit(value)

    async def _emit_with_result(self, event, data=None, namespace=None):
        try:
            return await super()._emit_with_result(event, data, namespace)

        except InvalidAction as e:
            await async_dialog.warning(self, "Invalid action", f"{e}")

        except ServerError:
            await async_dialog.warning(self, "Server error",
                                       "An error occurred on the server while processing your request.")

        except NotAuthorizedForAction:
            await async_dialog.warning(self, "Unauthorized",
                                       "You're not authorized to perform that action.")

    async def on_connect(self):
        await super().on_connect()
        self.Connect.emit()

    async def on_connect_error(self, error_message: str):
        await super().on_connect_error(error_message)
        self.ConnectError.emit()

    async def on_disconnect(self):
        await super().on_disconnect()
        self.Disconnect.emit()

    async def on_game_session_updated(self, data):
        await super().on_game_session_updated(data)
        self.GameSessionUpdated.emit(self._current_game_session)

    async def login_to_discord(self):
        if self.discord is None:
            raise RuntimeError("Missing Discord configuration for Randovania")
        await self.discord.start()
        authorize = await self.discord.authorize(self.configuration["discord_client_id"], ['identify'])
        new_session = await self._emit_with_result("login_with_discord", authorize["data"]["code"])
        await self.on_new_session(new_session)

    async def login_as_guest(self):
        new_session = await self._emit_with_result("login_with_guest")
        await self.on_new_session(new_session)

    async def on_game_update_notification(self, details):
        self.GameUpdateNotification.emit()
