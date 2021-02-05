import asyncio
import base64
import hashlib
import json
import logging
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import aiofiles
import aiohttp.client_exceptions
import engineio
import socketio
import socketio.exceptions

import randovania
from randovania.game_connection.backend_choice import GameBackendChoice
from randovania.game_connection.connection_base import InventoryItem, GameConnectionStatus
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.network_client.game_session import GameSessionListEntry, GameSessionEntry, User
from randovania.network_common.admin_actions import SessionAdminUserAction, SessionAdminGlobalAction
from randovania.network_common.error import decode_error, InvalidSession


class ConnectionState(Enum):
    Disconnected = "Disconnected"
    Connecting = "Connecting"
    Connected = "Connected"
    ConnectedNotLogged = "Connected, not logged in"
    ConnectedRestoringSession = "Connected, restoring session"

    @property
    def is_disconnected(self) -> bool:
        return self in (ConnectionState.Disconnected, ConnectionState.Connecting)


def _hash_address(server_address: str) -> str:
    return base64.urlsafe_b64encode(hashlib.blake2b(server_address.encode("utf-8"),
                                                    digest_size=12).digest()).decode("utf-8")


class UnableToConnect(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class NetworkClient:
    sio: socketio.AsyncClient
    _current_game_session: Optional[GameSessionEntry] = None
    _current_user: Optional[User] = None
    _connection_state: ConnectionState
    _call_lock: asyncio.Lock
    _connect_task: Optional[asyncio.Task] = None
    _waiting_for_on_connect: Optional[asyncio.Future] = None
    _restore_session_task: Optional[asyncio.Task] = None
    _connect_error: Optional[str] = None
    _last_self_update: Any = None

    def __init__(self, user_data_dir: Path, configuration: dict):
        self.logger = logging.getLogger(__name__)

        self._connection_state = ConnectionState.Disconnected
        self.sio = socketio.AsyncClient()
        self._call_lock = asyncio.Lock()

        self.configuration = configuration
        encoded_address = _hash_address(self.configuration["server_address"])
        self.server_data_path = user_data_dir / encoded_address
        self.session_data_path = self.server_data_path / "session_persistence.bin"

        self.sio.on('connect', self.on_connect)
        self.sio.on('connect_error', self.on_connect_error)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('user_session_update', self.on_user_session_updated)
        self.sio.on('game_session_update', self.on_game_session_updated)
        self.sio.on('game_has_update', self.on_game_update_notification)

    @property
    def connection_state(self) -> ConnectionState:
        return self._connection_state

    @connection_state.setter
    def connection_state(self, value: ConnectionState):
        self.logger.debug(f"updated connection_state: {value.value}")
        self._connection_state = value

    async def read_persisted_session(self) -> Optional[bytes]:
        try:
            async with aiofiles.open(self.session_data_path, "rb") as open_file:
                return await open_file.read()

        except FileNotFoundError:
            return None

    def has_previous_session(self) -> bool:
        return self.session_data_path.is_file()

    async def connect_if_authenticated(self):
        if self.session_data_path.is_file():
            self.logger.debug("session data exists")
            try:
                return await self.connect_to_server()
            except UnableToConnect:
                pass
        else:
            self.logger.debug("no session data")

    async def _internal_connect_to_server(self):
        if self.sio.connected:
            return

        waiting_for_on_connect = asyncio.get_running_loop().create_future()
        self._waiting_for_on_connect = waiting_for_on_connect
        try:
            # sio.connect is raising a NotImplementedError, likely due to Windows and/or asyncqt?
            engineio.asyncio_client.async_signal_handler_set = True

            self.connection_state = ConnectionState.Connecting
            # self.logger.info(f"connect_to_server: sleeping")
            # await asyncio.sleep(1)
            # self.logger.info(f"connect_to_server: sleep over")

            self.logger.info(f"connecting to {self.configuration['server_address']}")
            self._connect_error = None
            await self.sio.connect(self.configuration["server_address"],
                                   socketio_path=self.configuration["socketio_path"],
                                   transports=['websocket'],
                                   headers={"X-Randovania-Version": randovania.VERSION})
            await waiting_for_on_connect
            self.logger.info(f"connected")

        except (socketio.exceptions.ConnectionError, aiohttp.client_exceptions.ContentTypeError) as e:
            self.logger.info(f"failed with {e} - {type(e)}")
            if self._connect_error is None:
                if isinstance(e, aiohttp.client_exceptions.ContentTypeError):
                    message = e.message
                else:
                    message = str(e)
                await self.on_connect_error(message)
            error = self._connect_error
            await self.sio.disconnect()
            raise UnableToConnect(error)

    def notify_on_connect(self, error_message: Optional[Exception]):
        if self._waiting_for_on_connect is not None:
            if error_message is None:
                self._waiting_for_on_connect.set_result(None)
            else:
                self._waiting_for_on_connect.set_exception(error_message)
            self._waiting_for_on_connect = None

    def connect_to_server(self) -> asyncio.Task:
        if self._connect_task is None:
            self._connect_task = asyncio.create_task(self._internal_connect_to_server())
            self._connect_task.add_done_callback(lambda _: setattr(self, "_connect_task", None))

        return self._connect_task

    async def disconnect_from_server(self):
        self.logger.debug(f"will disconnect")
        await self.sio.disconnect()
        self.logger.debug(f"disconnected")

    async def _restore_session(self):
        persisted_session = await self.read_persisted_session()
        if persisted_session is not None:
            if self._current_game_session is not None:
                session_id = self._current_game_session.id
            else:
                session_id = None
            try:
                self.connection_state = ConnectionState.ConnectedRestoringSession
                self.logger.debug(f"session restoring session, with id {session_id}")
                await self.on_user_session_updated(await self._emit_with_result("restore_user_session",
                                                                                (persisted_session, session_id)))

                if self._current_game_session is not None:
                    await self.on_game_session_updated(
                        await self._emit_with_result("game_session_request_update", self._current_game_session.id))
                    await self.on_game_update_notification({})

                self.logger.info(f"session restored successful")
                self.connection_state = ConnectionState.Connected
            except InvalidSession:
                self.logger.info(f"invalid session, deleting")
                self.connection_state = ConnectionState.ConnectedNotLogged
                self.session_data_path.unlink()
        else:
            self.logger.info(f"no session to restore")
            self.connection_state = ConnectionState.ConnectedNotLogged

    async def on_connect(self):
        try:
            self._restore_session_task = asyncio.create_task(self._restore_session())
            self._restore_session_task.add_done_callback(lambda _: setattr(self, "_restore_session_task", None))
            await self._restore_session_task
        finally:
            self.notify_on_connect(None)

    async def on_connect_error(self, error_message: str):
        if isinstance(error_message, dict) and "message" in error_message:
            error_message = error_message["message"]

        try:
            self._connect_error = error_message
            self.logger.warning(error_message)
            self.connection_state = ConnectionState.Disconnected
            if self._restore_session_task is not None:
                self._restore_session_task.cancel()
        finally:
            self.notify_on_connect(socketio.exceptions.ConnectionError(error_message))

    async def on_disconnect(self):
        self.logger.info(f"on_disconnect")
        self.connection_state = ConnectionState.Disconnected
        if self._restore_session_task is not None:
            self._restore_session_task.cancel()

    async def on_user_session_updated(self, new_session: dict):
        self._current_user = User.from_json(new_session["user"])
        if self.connection_state in (ConnectionState.ConnectedRestoringSession, ConnectionState.ConnectedNotLogged):
            self.connection_state = ConnectionState.Connected

        self.logger.info(f"{self._current_user.name}, state: {self.connection_state}")

        encoded_session_data = base64.b85decode(new_session["encoded_session_b85"])
        self.server_data_path.mkdir(exist_ok=True, parents=True)
        async with aiofiles.open(self.session_data_path, "wb") as open_file:
            await open_file.write(encoded_session_data)

    async def on_game_session_updated(self, data):
        self._current_game_session = GameSessionEntry.from_json(data)
        self.logger.debug(f"{self._current_game_session.id}")

    async def on_game_update_notification(self, details):
        pass

    async def _emit_with_result(self, event, data=None, namespace=None):
        if self.connection_state.is_disconnected:
            self.logger.debug(f"{event}, urgent connect start")
            await self.connect_to_server()
            self.logger.debug(f"{event}, urgent connect finished")

        self.logger.debug(f"{event}, getting lock")
        async with self._call_lock:
            self.logger.debug(f"{event}, will call")
            result = await self.sio.call(event, data, namespace=namespace, timeout=30)

        if result is None:
            return None

        possible_error = decode_error(result)
        if possible_error is None:
            return result["result"]
        else:
            raise possible_error

    async def game_session_collect_locations(self, locations: Tuple[int, ...]):
        await self._emit_with_result("game_session_collect_locations",
                                     (self._current_game_session.id, locations))

    async def game_session_request_pickups(self) -> List[Tuple[str, bytes]]:
        data = await self._emit_with_result("game_session_request_pickups", self._current_game_session.id)
        return [
            (item["provider_name"], base64.b85decode(item["pickup"]))
            for item in data
            if item is not None
        ]

    async def get_game_session_list(self) -> List[GameSessionListEntry]:
        return [
            GameSessionListEntry.from_json(item)
            for item in await self._emit_with_result("list_game_sessions")
        ]

    async def create_new_session(self, session_name: str) -> GameSessionEntry:
        result = await self._emit_with_result("create_game_session", session_name)
        self._current_game_session = GameSessionEntry.from_json(result)
        return self._current_game_session

    async def join_game_session(self, session: GameSessionListEntry, password: Optional[str]):
        result = await self._emit_with_result("join_game_session", (session.id, password))
        self._current_game_session = GameSessionEntry.from_json(result)

    async def leave_game_session(self, permanent: bool):
        if permanent:
            await self.session_admin_player(self._current_user.id, SessionAdminUserAction.KICK, None)
        await self._emit_with_result("disconnect_game_session", self._current_game_session.id)
        self._current_game_session = None
        self._last_self_update = None

    async def session_admin_global(self, action: SessionAdminGlobalAction, arg):
        return await self._emit_with_result("game_session_admin_session",
                                            (self._current_game_session.id, action.value, arg))

    async def session_admin_player(self, user_id: int, action: SessionAdminUserAction, arg):
        return await self._emit_with_result("game_session_admin_player",
                                            (self._current_game_session.id, user_id, action.value, arg))

    async def session_self_update(self,
                                  inventory: Dict[ItemResourceInfo, InventoryItem],
                                  state: GameConnectionStatus, backend: GameBackendChoice):

        inventory_json = json.dumps([
            {"index": resource.index, "amount": item.amount, "capacity": item.capacity}
            for resource, item in inventory.items()
        ])
        state_string = f"{state.pretty_text} ({backend.pretty_text})"

        if self._last_self_update != state_string:
            await self._emit_with_result("game_session_self_update",
                                         (self._current_game_session.id, inventory_json, state_string))
            self._last_self_update = state_string

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    @property
    def current_game_session(self) -> Optional[GameSessionEntry]:
        return self._current_game_session
