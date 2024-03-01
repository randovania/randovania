from __future__ import annotations

import asyncio
import base64
import functools
import hashlib
import logging
import ssl
import time
import uuid
from enum import Enum
from typing import TYPE_CHECKING

import aiofiles
import aiohttp
import construct
import sentry_sdk
import socketio
import socketio.exceptions

import randovania
from randovania.bitpacking import bitpacking, construct_pack
from randovania.game_description import default_database
from randovania.games.game import RandovaniaGame
from randovania.lib import container_lib
from randovania.network_common import (
    admin_actions,
    connection_headers,
    error,
    multiplayer_session,
    pickup_serializer,
    remote_inventory,
    signals,
)
from randovania.network_common.multiplayer_session import (
    MultiplayerSessionActions,
    MultiplayerSessionAuditLog,
    MultiplayerSessionEntry,
    MultiplayerSessionListEntry,
    MultiplayerWorldPickups,
    User,
    WorldUserInventory,
)
from randovania.network_common.world_sync import ServerSyncRequest, ServerSyncResponse

if TYPE_CHECKING:
    from pathlib import Path


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
    return base64.urlsafe_b64encode(hashlib.blake2b(server_address.encode("utf-8"), digest_size=12).digest()).decode(
        "utf-8"
    )


def _decode_pickup(d: str, resource_database):
    decoder = bitpacking.BitPackDecoder(base64.b85decode(d))
    return pickup_serializer.BitPackPickupEntry.bit_pack_unpack(decoder, resource_database)


class UnableToConnect(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


_MINIMUM_TIMEOUT = 30
_MAXIMUM_TIMEOUT = 180
_TIMEOUTS_TO_DISCONNECT = 4
_TIMEOUT_STEP = 10

isrgrootx1 = """-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4
WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJu
ZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBY
MTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK3oJHP0FDfzm54rVygc
h77ct984kIxuPOZXoHj3dcKi/vVqbvYATyjb3miGbESTtrFj/RQSa78f0uoxmyF+
0TM8ukj13Xnfs7j/EvEhmkvBioZxaUpmZmyPfjxwv60pIgbz5MDmgK7iS4+3mX6U
A5/TR5d8mUgjU+g4rk8Kb4Mu0UlXjIB0ttov0DiNewNwIRt18jA8+o+u3dpjq+sW
T8KOEUt+zwvo/7V3LvSye0rgTBIlDHCNAymg4VMk7BPZ7hm/ELNKjD+Jo2FR3qyH
B5T0Y3HsLuJvW5iB4YlcNHlsdu87kGJ55tukmi8mxdAQ4Q7e2RCOFvu396j3x+UC
B5iPNgiV5+I3lg02dZ77DnKxHZu8A/lJBdiB3QW0KtZB6awBdpUKD9jf1b0SHzUv
KBds0pjBqAlkd25HN7rOrFleaJ1/ctaJxQZBKT5ZPt0m9STJEadao0xAH0ahmbWn
OlFuhjuefXKnEgV4We0+UXgVCwOPjdAvBbI+e0ocS3MFEvzG6uBQE3xDk3SzynTn
jh8BCNAw1FtxNrQHusEwMFxIt4I7mKZ9YIqioymCzLq9gwQbooMDQaHWBfEbwrbw
qHyGO0aoSCqI3Haadr8faqU9GY/rOPNk3sgrDQoo//fb4hVC1CLQJ13hef4Y53CI
rU7m2Ys6xt0nUW7/vGT1M0NPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNV
HRMBAf8EBTADAQH/MB0GA1UdDgQWBBR5tFnme7bl5AFzgAiIyBpY9umbbjANBgkq
hkiG9w0BAQsFAAOCAgEAVR9YqbyyqFDQDLHYGmkgJykIrGF1XIpu+ILlaS/V9lZL
ubhzEFnTIZd+50xx+7LSYK05qAvqFyFWhfFQDlnrzuBZ6brJFe+GnY+EgPbk6ZGQ
3BebYhtF8GaV0nxvwuo77x/Py9auJ/GpsMiu/X1+mvoiBOv/2X/qkSsisRcOj/KK
NFtY2PwByVS5uCbMiogziUwthDyC3+6WVwW6LLv3xLfHTjuCvjHIInNzktHCgKQ5
ORAzI4JMPJ+GslWYHb4phowim57iaztXOoJwTdwJx4nLCgdNbOhdjsnvzqvHu7Ur
TkXWStAmzOVyyghqpZXjFaH3pO3JLF+l+/+sKAIuvtd7u+Nxe5AW0wdeRlN8NwdC
jNPElpzVmbUq4JUagEiuTDkHzsxHpFKVK7q4+63SM1N95R1NbdWhscdCb+ZAJzVc
oyi3B43njTOQ5yOf+1CceWxG1bQVs5ZufpsMljq4Ui0/1lvh+wjChP4kqKOJ2qxq
4RgqsahDYVvTH9w7jXbyLeiNdd8XM2w9U/t7y0Ff/9yi0GE44Za4rF2LN9d11TPA
mRGunUHBcnWEvgJBQl9nJEiU0Zsnvgc/ubhPgXRR4Xq37Z0j4r7g1SgEEzwxA57d
emyPxgcYxn/eR44/KJ4EBs+lVDR3veyJm+kXQ99b21/+jh5Xos1AnX5iItreGCc=
-----END CERTIFICATE-----"""


class NetworkClient:
    sio: socketio.AsyncClient
    _current_user: User | None = None
    _connection_state: ConnectionState
    _call_lock: asyncio.Lock
    _connect_lock: asyncio.Lock
    _waiting_for_on_connect: asyncio.Future | None = None
    _restore_session_task: asyncio.Task | None = None
    _connect_error: str | None = None
    _num_emit_failures: int = 0
    _sessions_interested_in: set[int]
    _tracking_worlds: set[tuple[uuid.UUID, int]]
    _allow_reporting_username: bool = False

    def __init__(self, user_data_dir: Path, configuration: dict):
        self.logger = logging.getLogger("NetworkClient")

        old_connect = aiohttp.ClientSession.ws_connect

        @functools.wraps(old_connect)
        def wrap_ws_connect(*args, **kwargs):
            if any("randovania.metroidprime.run" in x for x in args if isinstance(x, str)):
                kwargs["ssl"] = ssl.create_default_context(cadata=isrgrootx1)
            return old_connect(*args, **kwargs)

        aiohttp.ClientSession.ws_connect = wrap_ws_connect

        self._connection_state = ConnectionState.Disconnected
        self.sio = socketio.AsyncClient(ssl_verify=configuration.get("verify_ssl", True), reconnection=False)
        self._call_lock = asyncio.Lock()
        self._connect_lock = asyncio.Lock()
        self._current_timeout = _MINIMUM_TIMEOUT
        self._sessions_interested_in = set()
        self._tracking_worlds = set()

        self.configuration = configuration
        encoded_address = _hash_address(self.configuration["server_address"])
        self.server_data_path = user_data_dir / encoded_address
        self.session_data_path = self.server_data_path / "session_persistence.bin"

        self.sio.on("connect", self.on_connect)
        self.sio.on("connect_error", self.on_connect_error)
        self.sio.on("disconnect", self.on_disconnect)
        self.sio.on("user_session_update", self.on_user_session_updated)
        self.sio.on(signals.SESSION_META_UPDATE, self._on_multiplayer_session_meta_update_raw)
        self.sio.on(signals.SESSION_ACTIONS_UPDATE, self._on_multiplayer_session_actions_update_raw)
        self.sio.on(signals.SESSION_AUDIT_UPDATE, self._on_multiplayer_session_audit_update_raw)
        self.sio.on(signals.WORLD_PICKUPS_UPDATE, self._on_world_pickups_update_raw)
        self.sio.on(signals.WORLD_BINARY_INVENTORY, self._on_world_user_inventory_raw)
        self.sio.on(signals.WORLD_JSON_INVENTORY, print)

    @property
    def connection_state(self) -> ConnectionState:
        return self._connection_state

    @connection_state.setter
    def connection_state(self, value: ConnectionState):
        self.logger.debug(f"updated connection_state: {value.value}")
        self._connection_state = value

    async def read_persisted_session(self) -> bytes | None:
        try:
            async with aiofiles.open(self.session_data_path, "rb") as open_file:
                return await open_file.read()

        except FileNotFoundError:
            return None

    def has_previous_session(self) -> bool:
        return self.session_data_path.is_file()

    async def _internal_connect_to_server(self) -> None:
        import aiohttp.client_exceptions

        if self.sio.connected:
            self.logger.debug("sio is already connected")
            return

        waiting_for_on_connect = asyncio.get_running_loop().create_future()
        self._waiting_for_on_connect = waiting_for_on_connect
        try:
            self.connection_state = ConnectionState.Connecting
            # self.logger.info(f"connect_to_server: sleeping")
            # await asyncio.sleep(1)
            # self.logger.info(f"connect_to_server: sleep over")

            self.logger.info(f"connecting to {self.configuration['server_address']}")
            self._connect_error = None
            self._num_emit_failures = 0
            await self.sio.connect(
                self.configuration["server_address"],
                socketio_path=self.configuration["socketio_path"],
                transports=["websocket"],
                headers=connection_headers(),
            )
            self.logger.info("sio.connect successful")
            await waiting_for_on_connect
            self.logger.info("connected")

        except (socketio.exceptions.ConnectionError, aiohttp.client_exceptions.ContentTypeError) as e:
            self.logger.info("failed with %s - %s", e, type(e))
            if self._connect_error is None:
                if isinstance(e, aiohttp.client_exceptions.ContentTypeError):
                    message = e.message
                else:
                    message = str(e)
                await self.on_connect_error(message)
            err = self._connect_error
            await self.sio.disconnect()
            raise UnableToConnect(err)

        except error.BaseNetworkError as e:
            self._connect_error = str(e)

            # During the `on_connect` event we perform extra queries that can be rejected by the
            # server (wrong version, etc.) which calls `sio.disconnect`. However, this is all during
            # `sio.connect` which will finish by setting `sio.connected = True`.
            await self.sio.disconnect()
            self.sio.connected = False
            raise

    def notify_on_connect(self, error_message: Exception | None):
        if self._waiting_for_on_connect is not None:
            if error_message is None:
                self._waiting_for_on_connect.set_result(None)
            else:
                self._waiting_for_on_connect.set_exception(error_message)
            self._waiting_for_on_connect = None

    async def connect_to_server(self) -> None:
        async with self._connect_lock:
            try:
                return await self._internal_connect_to_server()
            except asyncio.CancelledError:
                return await self.disconnect_from_server()

    async def disconnect_from_server(self):
        self.logger.debug("will disconnect")
        await self.sio.disconnect()
        self.logger.debug("disconnected. sio connected? %s", self.sio.connected)

    async def _restore_session(self):
        persisted_session = await self.read_persisted_session()
        if persisted_session is not None:
            try:
                self.connection_state = ConnectionState.ConnectedRestoringSession
                self.logger.debug("session restoring session")
                await self.on_user_session_updated(
                    await self.server_call("restore_user_session", persisted_session, handle_invalid_session=False)
                )

                # re-join rooms
                self.logger.info("calling listen to session for %s", self._sessions_interested_in)
                for session_id in list(self._sessions_interested_in):
                    await self.server_call("multiplayer_listen_to_session", (session_id, True))
                for world_uid, user_id in list(self._tracking_worlds):
                    await self.server_call("multiplayer_watch_inventory", (str(world_uid), user_id, True, True))

                self.logger.info("session restored successful")

                self.connection_state = ConnectionState.Connected

            except (error.InvalidSessionError, error.UserNotAuthorizedToUseServerError) as e:
                self.logger.info(
                    "session not authorized, deleting"
                    if isinstance(e, error.UserNotAuthorizedToUseServerError)
                    else "invalid session, deleting"
                )
                self.connection_state = ConnectionState.ConnectedNotLogged
                self.session_data_path.unlink()

        else:
            self.logger.info("no session to restore")
            self.connection_state = ConnectionState.ConnectedNotLogged

    async def on_connect(self):
        self.logger.debug("Received on_connect")
        error_message = None
        try:
            self._restore_session_task = asyncio.create_task(self._restore_session())
            self._restore_session_task.add_done_callback(lambda _: setattr(self, "_restore_session_task", None))
            await self._restore_session_task

        except error.BaseNetworkError as e:
            self.logger.warning(f"Unable to restore session after logging in, give up! Reason: {e}")
            error_message = e
            self.connection_state = ConnectionState.Disconnected
            await self.disconnect_from_server()

        finally:
            self.notify_on_connect(error_message)

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
        self.logger.info("on_disconnect")
        self.connection_state = ConnectionState.Disconnected
        if self._restore_session_task is not None:
            self._restore_session_task.cancel()

    async def on_user_session_updated(self, new_session: dict):
        self._current_user = User.from_json(new_session["user"])
        self._update_reported_username()

        if self.connection_state == ConnectionState.ConnectedNotLogged:
            self.connection_state = ConnectionState.Connected

        self.logger.info(f"{self._current_user.name}, state: {self.connection_state}")

        encoded_session_data = base64.b85decode(new_session["encoded_session_b85"])
        self.server_data_path.mkdir(exist_ok=True, parents=True)
        async with aiofiles.open(self.session_data_path, "wb") as open_file:
            await open_file.write(encoded_session_data)

    # Multiplayer Session Updated

    async def _on_multiplayer_session_meta_update_raw(self, data: dict):
        entry = MultiplayerSessionEntry.from_json(data)
        self.logger.debug("%s: %s", entry.id, hashlib.blake2b(str(data).encode("utf-8")).hexdigest())
        await self.on_multiplayer_session_meta_update(entry)

    async def on_multiplayer_session_meta_update(self, entry: MultiplayerSessionEntry):
        self.logger.info("name: %s, users: %d, game: %s", entry.name, len(entry.users), str(entry.game_details))

    async def _on_multiplayer_session_actions_update_raw(self, data: bytes):
        await self.on_multiplayer_session_actions_update(
            construct_pack.decode(data, multiplayer_session.MultiplayerSessionActions)
        )

    async def on_multiplayer_session_actions_update(self, actions: MultiplayerSessionActions):
        self.logger.info("num actions: %d", len(actions.actions))

    async def _on_multiplayer_session_audit_update_raw(self, data: bytes):
        await self.on_multiplayer_session_audit_update(
            construct_pack.decode(data, multiplayer_session.MultiplayerSessionAuditLog)
        )

    async def on_multiplayer_session_audit_update(self, audit_log: MultiplayerSessionAuditLog):
        self.logger.info("num audit: %d", len(audit_log.entries))

    # World Events
    async def _on_world_pickups_update_raw(self, data):
        game = RandovaniaGame(data["game"])
        resource_database = default_database.resource_database_for(game)

        await self.on_world_pickups_update(
            MultiplayerWorldPickups(
                world_id=uuid.UUID(data["world"]),
                game=game,
                pickups=tuple(
                    (item["provider_name"], _decode_pickup(item["pickup"], resource_database))
                    for item in data["pickups"]
                ),
            )
        )

    async def on_world_pickups_update(self, pickups: MultiplayerWorldPickups):
        self.logger.info("world %s, num pickups: %d", pickups.world_id, len(pickups.pickups))

    async def _on_world_user_inventory_raw(self, entry_id: str, user_id: int, raw_inventory: bytes):
        inventory_or_error = remote_inventory.decode_remote_inventory(raw_inventory)
        if isinstance(inventory_or_error, construct.ConstructError):
            self.logger.debug("Unable to parse inventory for entry %d: %s", entry_id, str(inventory_or_error))
            return
        else:
            inventory = inventory_or_error

        session_inventory = WorldUserInventory(
            world_id=uuid.UUID(entry_id),
            user_id=user_id,
            inventory=inventory,
        )
        await self.on_world_user_inventory(session_inventory)

    async def on_world_user_inventory(self, inventory: WorldUserInventory):
        pass

    def _update_timeout_with(self, request_time: float, success: bool):
        if success:
            if request_time < self._current_timeout - _TIMEOUT_STEP and self._current_timeout > _MINIMUM_TIMEOUT:
                self._current_timeout -= _TIMEOUT_STEP
                self.logger.debug(f"decreasing timeout by {_TIMEOUT_STEP}, to {self._current_timeout}")
        else:
            self._current_timeout += _TIMEOUT_STEP
            self._num_emit_failures += 1
            self.logger.debug(f"increasing timeout by {_TIMEOUT_STEP}, to {self._current_timeout}")

        self._current_timeout = min(max(self._current_timeout, _MINIMUM_TIMEOUT), _MAXIMUM_TIMEOUT)

    async def server_call(self, event: str, data=None, *, namespace=None, handle_invalid_session: bool = True):
        self.logger.debug("performing call for %s", event)

        if self.connection_state.is_disconnected:
            self.logger.debug("%s, urgent connect start. Sio is connected? %s", event, self.sio.connected)
            await self.connect_to_server()
            self.logger.debug("%s, urgent connect finished", event)

        async with self._call_lock:
            request_start = time.time()
            timeout = self._current_timeout
            self.logger.debug("%s, will call with timeout %d", event, timeout)
            try:
                result = await self.sio.call(event, data, namespace=namespace, timeout=timeout)
                request_time = time.time() - request_start
                self._update_timeout_with(request_time, True)

            except socketio.exceptions.TimeoutError:
                request_time = time.time() - request_start
                self._update_timeout_with(request_time, False)
                if self._num_emit_failures >= _TIMEOUTS_TO_DISCONNECT:
                    # If getting too many timeouts in a row, just disconnect so the user is aware something is wrong.
                    await self.disconnect_from_server()
                raise error.RequestTimeoutError(f"Timeout after {request_time:.2f}s, with a timeout of {timeout}.")

        if result is None:
            return None

        possible_error = error.BaseNetworkError.from_json(result)
        if possible_error is None:
            return result["result"]
        else:
            if handle_invalid_session and isinstance(possible_error, error.InvalidSessionError):
                self.logger.info("Received InvalidSession during a %s call", event)
                await self.logout()

            raise possible_error

    async def get_multiplayer_session_list(self, ignore_limit: bool) -> list[MultiplayerSessionListEntry]:
        return [
            MultiplayerSessionListEntry.from_json(item)
            for item in await self.server_call("multiplayer_list_sessions", (None if ignore_limit else 100,))
        ]

    def _with_new_session(self, data: dict) -> MultiplayerSessionEntry:
        result = MultiplayerSessionEntry.from_json(data)
        self._sessions_interested_in.add(result.id)
        return result

    async def create_new_session(self, session_name: str) -> MultiplayerSessionEntry:
        result = await self.server_call("multiplayer_create_session", session_name)
        return self._with_new_session(result)

    async def join_multiplayer_session(self, session_id: int, password: str | None):
        result = await self.server_call("multiplayer_join_session", (session_id, password))
        return self._with_new_session(result)

    async def listen_to_session(self, session_id: int, listen: bool):
        result = await self.server_call("multiplayer_listen_to_session", (session_id, listen))
        container_lib.ensure_in_set(session_id, self._sessions_interested_in, listen)
        return result

    async def session_admin_global(
        self, session: MultiplayerSessionEntry, action: admin_actions.SessionAdminGlobalAction, arg
    ):
        return await self.server_call("multiplayer_admin_session", (session.id, action.value, arg))

    async def session_admin_player(
        self, session: MultiplayerSessionEntry, user_id: int, action: admin_actions.SessionAdminUserAction, arg
    ):
        return await self.server_call("multiplayer_admin_player", (session.id, user_id, action.value, arg))

    async def world_track_inventory(self, world_uid: uuid.UUID, user_id: int, enable: bool):
        await self.server_call("multiplayer_watch_inventory", (str(world_uid), user_id, enable, True))
        container_lib.ensure_in_set((world_uid, user_id), self._tracking_worlds, enable)

    async def perform_world_sync(self, request: ServerSyncRequest) -> ServerSyncResponse:
        return construct_pack.decode(
            await self.server_call("multiplayer_world_sync", construct_pack.encode(request)),
            ServerSyncResponse,
        )

    @property
    def current_user(self) -> User | None:
        return self._current_user

    @property
    def current_user_id(self) -> int | None:
        if self._current_user is not None:
            return self._current_user.id
        return None

    async def logout(self):
        self.logger.info("Logging out")
        self.session_data_path.unlink()
        self._current_user = None
        self._update_reported_username()

        if self.connection_state != ConnectionState.Connected:
            return
        self.connection_state = ConnectionState.ConnectedNotLogged
        await self.server_call("logout")

    def _update_reported_username(self):
        if self.allow_reporting_username and self._current_user and self._current_user.discord_id:
            sentry_sdk.set_user(
                {
                    "id": self._current_user.discord_id,
                    "username": self._current_user.name,
                    "server_id": self._current_user.id,
                }
            )
        else:
            sentry_sdk.set_user(None)

    @property
    def last_connection_error(self) -> str | None:
        return self._connect_error

    @property
    def allow_reporting_username(self):
        return self._allow_reporting_username or randovania.is_dev_version()

    @allow_reporting_username.setter
    def allow_reporting_username(self, value):
        self._allow_reporting_username = value
        self._update_reported_username()
