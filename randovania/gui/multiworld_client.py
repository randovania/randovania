import asyncio
import dataclasses
import logging
import uuid
from pathlib import Path

from PySide6.QtCore import QObject
from frozendict import frozendict
from qasync import asyncSlot

from randovania.bitpacking import construct_pack
from randovania.game_connection.game_connection import GameConnection, ConnectedGameState
from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.interface_common.players_configuration import INVALID_UUID
from randovania.network_client.network_client import UnableToConnect, ConnectionState
from randovania.network_common import error
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.multiplayer_session import MultiplayerWorldPickups, RemoteInventory
from randovania.interface_common.world_database import WorldData, WorldDatabase, WorldServerData
from randovania.network_common.world_sync import ServerWorldSync, ServerSyncRequest


class MultiworldClient(QObject):
    _persist_path: Path
    _sync_task: asyncio.Task | None = None
    _remote_games: dict[uuid.UUID, MultiplayerWorldPickups]

    _last_reported_status: dict[uuid.UUID, GameConnectionStatus]
    _recently_connected: bool = True
    _last_sync: ServerSyncRequest = ServerSyncRequest(worlds=frozendict({}))

    def __init__(self, network_client: QtNetworkClient, game_connection: GameConnection, database: WorldDatabase):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.network_client = network_client
        self.game_connection = game_connection
        self.database = database
        self._remote_games = {}
        self._last_reported_status = {}
        self._pickups_lock = asyncio.Lock()

        self.game_connection.GameStateUpdated.connect(self.on_game_state_updated)
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

            sync_requests[state.id] = ServerWorldSync(
                status=state.status,
                collected_locations=self.database.get_locations_to_upload(state.id),
                inventory=(
                    construct_pack.encode(
                        {item.short_name: item_state
                         for item, item_state in state.current_inventory.items()},
                        RemoteInventory
                    )
                    if state.status == GameConnectionStatus.InGame else None
                ),
                request_details=state.id not in self._remote_games,
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

        return ServerSyncRequest(
            worlds=frozendict(sync_requests),
        )

    async def _server_sync(self):
        while True:
            # Wait a bit, in case a RemoteConnector is sending multiple events in quick succession
            await asyncio.sleep(1)

            if self._recently_connected:
                self._recently_connected = False
                self._last_sync = ServerSyncRequest(worlds=frozendict({}))

            request = self._create_new_sync_request()
            if request == self._last_sync:
                self.logger.debug("Skipping server sync: no changes from last time")
                return

            try:
                result = await self.network_client.perform_world_sync(request)
            except (Exception, UnableToConnect) as e:
                message = f"Exception {type(e)} when attempting to sync locations."
                if isinstance(e, (UnableToConnect, error.NotLoggedIn, error.InvalidSession, error.RequestTimeout)):
                    self.logger.warning(message)
                else:
                    self.logger.exception(message)
                await asyncio.sleep(5)
                continue

            modified_data: dict[uuid.UUID, WorldData] = {}

            def get_data(u: uuid.UUID):
                if u not in modified_data:
                    modified_data[u] = self.database.get_data_for(u)
                return modified_data[u]

            for uid, world in request.worlds.items():
                if uid in result.errors:
                    continue

                self._last_reported_status[uid] = world.status
                if world.collected_locations:
                    modified_data[uid] = get_data(uid).extend_uploaded_locations(
                        world.collected_locations
                    )

            for uid, world in result.worlds.items():
                modified_data[uid] = dataclasses.replace(
                    get_data(uid),
                    server_data=WorldServerData(
                        world_name=world.world_name,
                        session_id=world.session.id,
                        session_name=world.session.name
                    )
                )

            self._last_sync = ServerSyncRequest(
                worlds=frozendict([
                    (uid, world)
                    for uid, world in request.worlds.items()
                    if uid not in result.errors
                ])
            )
            if result.errors:
                for uid, err in result.errors.items():
                    # TODO: some better visibility for these errors would be great
                    message = f"Exception {type(err)} when attempting to sync {uid}."
                    if isinstance(err, (UnableToConnect, error.NotLoggedIn, error.InvalidSession, error.RequestTimeout)
                                  ):
                        self.logger.warning(message)
                    else:
                        self.logger.exception(message)

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

    @asyncSlot(MultiplayerWorldPickups)
    async def on_network_game_updated(self, pickups: MultiplayerWorldPickups):
        async with self._pickups_lock:
            self._remote_games[pickups.world_id] = pickups

        for connector in self.game_connection.connected_states.keys():
            if connector.layout_uuid == pickups.world_id:
                await connector.set_remote_pickups(pickups.pickups)

        self.start_server_sync_task()

    def on_connection_state_updated(self, state: ConnectionState):
        if state == ConnectionState.Connected:
            self._recently_connected = True
            self.start_server_sync_task()
