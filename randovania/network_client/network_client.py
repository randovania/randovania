import asyncio
import base64
import logging
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

import aiofiles
import aiohttp.client_exceptions
import engineio
import socketio
import socketio.exceptions

import randovania
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.network_client.game_session import GameSessionListEntry, GameSessionEntry, User
from randovania.network_common.admin_actions import SessionAdminUserAction, SessionAdminGlobalAction
from randovania.network_common.error import decode_error, InvalidSession


class ConnectionState(Enum):
    Disconnected = "Disconnected"
    Connecting = "Connecting"
    Connected = "Connected"
    ConnectedNotLogged = "Connected, not logged in"
    ConnectedRestoringSession = "Connected, restoring session"
    Reconnecting = "Connection lost, reconnecting"
    UnableToConnect = "Unable to connect"


class NetworkClient:
    sio: socketio.AsyncClient
    _current_game_session: Optional[GameSessionEntry] = None
    _current_user: Optional[User] = None
    _connection_state: ConnectionState
    _was_connected: bool = False
    _call_lock: asyncio.Lock

    def __init__(self, user_data_dir: Path):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self._connection_state = ConnectionState.Disconnected
        self.sio = socketio.AsyncClient()
        self._call_lock = asyncio.Lock()

        self.configuration = randovania.get_configuration()
        encoded_address = base64.urlsafe_b64encode(self.configuration["server_address"].encode("utf-8")).decode("utf-8")
        self.session_data_path = user_data_dir / encoded_address / "session_persistence.bin"

        self.sio.on('connect', self.on_connect)
        self.sio.on('connect_error', self.on_connect_error)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('new_session', self.on_new_session)
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

    async def connect_if_authenticated(self):
        if self.session_data_path.is_file():
            self.logger.info("connect_if_authenticated: session data exists")
            return await self.connect_to_server()
        else:
            self.logger.info("connect_if_authenticated: no session data")

    async def connect_to_server(self):
        # TODO: failing at the first time means it isn't continuosly retried automatically
        try:
            # sio.connect is raising a NotImplementedError, likely due to Windows and/or asyncqt?
            engineio.asyncio_client.async_signal_handler_set = True

            self.connection_state = ConnectionState.Connecting
            self.logger.info(f"connect_to_server: connecting")
            await self.sio.connect(self.configuration["server_address"],
                                   socketio_path=self.configuration["socketio_path"],
                                   headers={"X-Randovania-Version": randovania.VERSION})
            self.logger.info(f"connect_to_server: connected")

        except (socketio.exceptions.ConnectionError, aiohttp.client_exceptions.ContentTypeError) as e:
            self.logger.info(f"connect_to_server: failed with {e}")

    async def disconnect_from_server(self):
        await self.sio.disconnect()
        self._was_connected = False

    async def on_connect(self):
        self._was_connected = True
        persisted_session = await self.read_persisted_session()
        if persisted_session is not None:
            if self._current_game_session is not None:
                session_id = self._current_game_session.id
            else:
                session_id = None
            try:
                self.connection_state = ConnectionState.ConnectedRestoringSession
                await self.on_new_session(await self._emit_with_result("restore_user_session",
                                                                       (persisted_session, session_id)))
                self.logger.info(f"on_connect: session restored successful")
                self.connection_state = ConnectionState.Connected
            except InvalidSession:
                self.logger.info(f"on_connect: invalid session, deleting")
                self.connection_state = ConnectionState.ConnectedNotLogged
                self.session_data_path.unlink()
        else:
            self.logger.info(f"on_connect: no session to restore")
            self.connection_state = ConnectionState.ConnectedNotLogged

    async def on_connect_error(self, error_message: str):
        self.logger.info(f"on_connect_error: {error_message}")
        if self._was_connected:
            self.connection_state = ConnectionState.Reconnecting
        else:
            self.connection_state = ConnectionState.UnableToConnect

    async def on_disconnect(self):
        self.logger.info(f"on_disconnect")
        self.connection_state = ConnectionState.Disconnected

    async def on_new_session(self, new_session: dict):
        self._current_user = User.from_json(new_session["user"])
        encoded_session_data = base64.b85decode(new_session["encoded_session_b85"])

        self.logger.info(f"on_new_session: {self._current_user.name}")

        self.session_data_path.parent.mkdir(exist_ok=True, parents=True)
        async with aiofiles.open(self.session_data_path, "wb") as open_file:
            await open_file.write(encoded_session_data)

    async def on_game_session_updated(self, data):
        self._current_game_session = GameSessionEntry.from_json(data)

    async def on_game_update_notification(self, details):
        pass

    async def _emit_with_result(self, event, data=None, namespace=None):
        async with self._call_lock:
            if self.connection_state == ConnectionState.Disconnected:
                await self.connect_to_server()
            self.logger.debug(f"_emit_with_result: {event}")
            result = await self.sio.call(event, data, namespace=namespace, timeout=30)

        if result is None:
            return None

        possible_error = decode_error(result)
        if possible_error is None:
            return result["result"]
        else:
            raise possible_error

    async def game_session_collect_pickup(self, location: PickupIndex) -> Optional[bytes]:
        maybe_pickup = await self._emit_with_result("game_session_collect_pickup",
                                                    (self._current_game_session.id, location.index))
        if maybe_pickup is not None:
            return base64.b85decode(maybe_pickup)

    async def game_session_request_pickups(self) -> List[Tuple[str, bytes]]:
        data = await self._emit_with_result("game_session_request_pickups", self._current_game_session.id)
        return [
            (item["message"], base64.b85decode(item["pickup"]))
            for item in data
            if item is not None
        ]

    async def get_game_session_list(self) -> List[GameSessionListEntry]:
        return [
            GameSessionListEntry(**item)
            for item in await self._emit_with_result("list_game_sessions")
        ]

    async def create_new_session(self, session_name: str) -> GameSessionEntry:
        result = await self._emit_with_result("create_game_session", session_name)
        self._current_game_session = GameSessionEntry.from_json(result)
        return self._current_game_session

    async def join_session(self, session: GameSessionListEntry, password: Optional[str]):
        result = await self._emit_with_result("join_game_session", (session.id, password))
        self._current_game_session = GameSessionEntry.from_json(result)

    async def leave_session(self, permanent: bool):
        await self._emit_with_result("leave_game_session", (self._current_game_session.id, permanent))
        self._current_game_session = None

    async def session_admin_global(self, session_id: int, action: SessionAdminGlobalAction, arg):
        return await self._emit_with_result("game_session_admin_session", (session_id, action.value, arg))

    async def session_admin_player(self, session_id: int, user_id: int, action: SessionAdminUserAction, arg):
        return await self._emit_with_result("game_session_admin_player", (session_id, user_id, action.value, arg))

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    @property
    def current_game_session(self) -> Optional[GameSessionEntry]:
        return self._current_game_session
