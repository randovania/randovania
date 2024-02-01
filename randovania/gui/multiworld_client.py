from __future__ import annotations

import asyncio
import dataclasses
import logging
from typing import TYPE_CHECKING

import construct
from frozendict import frozendict
from PySide6 import QtCore
from qasync import asyncSlot

from randovania.game_connection.game_connection import ConnectedGameState, GameConnection
from randovania.interface_common.players_configuration import INVALID_UUID
from randovania.interface_common.world_database import WorldData, WorldDatabase, WorldServerData
from randovania.network_client.network_client import ConnectionState, UnableToConnect
from randovania.network_common import error, remote_inventory
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.multiplayer_session import (
    MultiplayerSessionEntry,
    MultiplayerWorldPickups,
)
from randovania.network_common.world_sync import ServerSyncRequest, ServerWorldSync

if TYPE_CHECKING:
    import uuid
    from pathlib import Path

    from randovania.gui.lib.qt_network_client import QtNetworkClient

_ERRORS_THAT_STOP_SYNC = (
    error.WorldDoesNotExistError,
    error.WorldNotAssociatedError,
)


class MultiworldClient(QtCore.QObject):
    _persist_path: Path
    _sync_task: asyncio.Task | None = None
    _remote_games: dict[uuid.UUID, MultiplayerWorldPickups]

    _last_reported_status: dict[uuid.UUID, GameConnectionStatus]
    _ignore_last_sync: bool = True
    _worlds_with_details: set[uuid.UUID]
    _world_sync_errors: dict[uuid.UUID, error.BaseNetworkError]
    _last_sync: ServerSyncRequest = ServerSyncRequest(worlds=frozendict({}))

    _last_sync_exception: Exception | None = None

    SyncFailure = QtCore.Signal()

    def __init__(self, network_client: QtNetworkClient, game_connection: GameConnection, database: WorldDatabase):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.network_client = network_client
        self.game_connection = game_connection
        self.database = database
        self._remote_games = {}
        self._last_reported_status = {}
        self._world_sync_errors = {}
        self._pickups_lock = asyncio.Lock()
        self._worlds_with_details = set()

        self.game_connection.GameStateUpdated.connect(self.on_game_state_updated)
        self.network_client.MultiplayerSessionMetaUpdated.connect(self.on_session_meta_update)
        self.network_client.WorldPickupsUpdated.connect(self.on_network_game_updated)
        self.network_client.ConnectionStateUpdated.connect(self.on_connection_state_updated)

    async def start(self):
        self.logger.debug("start")

        self.start_server_sync_task()

    async def stop(self):
        self.logger.debug("stop")

        if self._sync_task is not None:
            self._sync_task.cancel()
            self._sync_task = None

    def _create_new_sync_request(self) -> ServerSyncRequest:
        sync_requests = {}

        for state in self.game_connection.connected_states.values():
            if state.id == INVALID_UUID:
                continue

            inventory = None
            if state.status == GameConnectionStatus.InGame:
                try:
                    inventory = remote_inventory.inventory_to_encoded_remote(state.current_inventory)
                except construct.ConstructError:
                    # TODO: display this somehow in the UI?
                    self.logger.exception("Unable to encode inventory for sync request")

            sync_requests[state.id] = ServerWorldSync(
                status=state.status,
                collected_locations=self.database.get_locations_to_upload(state.id),
                inventory=inventory,
                request_details=state.id not in self._worlds_with_details,
            )

        # Check for all games that were connected at some point, and upload any pending location from them.
        for uid in self.database.all_known_data():
            if uid not in sync_requests and (locations := self.database.get_locations_to_upload(uid)):
                sync_requests[uid] = ServerWorldSync(
                    status=GameConnectionStatus.Disconnected,
                    collected_locations=locations,
                    inventory=None,
                    request_details=False,
                )

        for uid, old_status in self._last_reported_status.items():
            if old_status != GameConnectionStatus.Disconnected and uid not in sync_requests:
                sync_requests[uid] = ServerWorldSync(
                    status=GameConnectionStatus.Disconnected,
                    collected_locations=self.database.get_locations_to_upload(uid),
                    inventory=None,
                    request_details=False,
                )

        for uid in set(sync_requests.keys()) & set(self._world_sync_errors.keys()):
            if isinstance(self._world_sync_errors[uid], _ERRORS_THAT_STOP_SYNC):
                self.logger.debug("Not syncing %s: had sync error", uid)
                sync_requests.pop(uid)

        return ServerSyncRequest(
            worlds=frozendict(sync_requests),
        )

    async def _server_sync(self):
        while True:
            # Wait a bit, in case a RemoteConnector is sending multiple events in quick succession
            await asyncio.sleep(1)

            if self._ignore_last_sync:
                self._ignore_last_sync = False
                self._last_sync = ServerSyncRequest(worlds=frozendict({}))

            request = self._create_new_sync_request()
            if request == self._last_sync:
                self.logger.debug("Skipping server sync: no changes from last time")
                return

            for uid, world_request in request.worlds.items():
                self.logger.debug(
                    "Syncing %s: State %s, collected %s", uid, world_request.status, world_request.collected_locations
                )

            try:
                result = await self.network_client.perform_world_sync(request)

            except (UnableToConnect, error.RequestTimeoutError, error.UnsupportedClientError) as e:
                self._update_sync_exception(e)
                self.logger.info("Can't sync worlds: Unable to connect to server: %s", e)
                await asyncio.sleep(15)
                continue

            except (error.NotLoggedInError, error.InvalidSessionError) as e:
                self._update_sync_exception(e)
                self.logger.info("Can't sync worlds: Not logged in")
                await asyncio.sleep(30)
                continue

            except Exception as e:
                self._update_sync_exception(e)
                self.logger.exception("Unexpected error syncing worlds: %s", e)
                await asyncio.sleep(15)
                continue

            self._last_sync_exception = None
            modified_data: dict[uuid.UUID, WorldData] = {}

            def get_data(u: uuid.UUID):
                if u not in modified_data:
                    modified_data[u] = self.database.get_data_for(u)
                return modified_data[u]

            for uid, world in request.worlds.items():
                if uid in result.errors:
                    continue

                self._last_reported_status[uid] = world.status
                self._world_sync_errors.pop(uid, None)
                if world.collected_locations:
                    modified_data[uid] = get_data(uid).extend_uploaded_locations(world.collected_locations)

            for uid, world in result.worlds.items():
                modified_data[uid] = dataclasses.replace(
                    get_data(uid),
                    server_data=WorldServerData(
                        world_name=world.world_name,
                        session_id=world.session_id,
                        session_name=world.session_name,
                    ),
                )
                self._worlds_with_details.add(uid)

            self._last_sync = ServerSyncRequest(
                worlds=frozendict([(uid, world) for uid, world in request.worlds.items() if uid not in result.errors])
            )

            if result.errors:
                for uid, err in result.errors.items():
                    self.logger.info("When syncing %s, received %s", uid, err)
                    self._world_sync_errors[uid] = err
                self.SyncFailure.emit()

            if modified_data:
                await self.database.set_many_data(modified_data)

            # Wait a bit, and try sending a new request in case new data came while waiting for the server response
            await asyncio.sleep(4)

    def start_server_sync_task(self):
        if self._sync_task is not None and not self._sync_task.done():
            return

        self._sync_task = asyncio.create_task(self._server_sync())

    @asyncSlot(ConnectedGameState)
    async def on_game_state_updated(self, state: ConnectedGameState):
        if state.id == INVALID_UUID:
            return

        our_indices: set[int] = {i.index for i in state.collected_indices}

        data = self.database.get_data_for(state.id)
        await self.database.set_data_for(state.id, data.extend_collected_location(our_indices))

        if state.id in self._remote_games:
            await state.source.set_remote_pickups(self._remote_games[state.id].pickups)

        self.start_server_sync_task()

    @asyncSlot(MultiplayerSessionEntry)
    async def on_session_meta_update(self, session: MultiplayerSessionEntry):
        worlds_by_id = {world.id for world in session.worlds}
        user_worlds = {}

        user = self.network_client.current_user
        if user is not None:
            user_details = session.users.get(user.id)
            if user_details is not None:
                user_worlds = user_details.worlds

        any_error_cleared = False
        for uid, err in list(self._world_sync_errors.items()):
            error_cleared = False
            match type(err):
                case error.WorldDoesNotExistError:
                    error_cleared = uid in worlds_by_id

                case error.WorldNotAssociatedError:
                    error_cleared = uid in user_worlds

            if error_cleared:
                any_error_cleared = True
                self._world_sync_errors.pop(uid)

        if any_error_cleared:
            self.SyncFailure.emit()

    @asyncSlot(MultiplayerWorldPickups)
    async def on_network_game_updated(self, pickups: MultiplayerWorldPickups):
        async with self._pickups_lock:
            self._remote_games[pickups.world_id] = pickups

        for connector in self.game_connection.connected_states.keys():
            if connector.layout_uuid == pickups.world_id:
                await connector.set_remote_pickups(pickups.pickups)

        self.start_server_sync_task()

    def on_connection_state_updated(self, state: ConnectionState):
        if state != ConnectionState.Connected:
            self._worlds_with_details.clear()

        if state in {ConnectionState.Connected, ConnectionState.Disconnected}:
            # If disconnected, cause a connection to upload what we have
            self._ignore_last_sync = True
            self.start_server_sync_task()

    @property
    def last_sync_exception(self):
        return self._last_sync_exception

    def get_world_sync_error(self, uid: uuid.UUID) -> error.BaseNetworkError | None:
        return self._world_sync_errors.get(uid)

    def _update_sync_exception(self, err: Exception | None):
        last = self._last_sync_exception
        self._last_sync_exception = err
        if last != err:
            self.SyncFailure.emit()
