import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import AsyncContextManager, Self

from PySide6.QtCore import QObject
from frozendict import frozendict
from qasync import asyncSlot

from randovania.bitpacking import construct_pack
from randovania.game_connection.game_connection import GameConnection, ConnectedGameState
from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.lib import json_lib
from randovania.network_client.network_client import UnableToConnect
from randovania.network_common import error
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.multiplayer_session import MultiplayerWorldPickups, RemoteInventory
from randovania.network_common.world_sync import ServerWorldSync, ServerSyncRequest


class Data(AsyncContextManager):
    collected_locations: set[int]
    uploaded_locations: set[int]
    latest_message_displayed: int

    def __init__(self, path: Path):
        self._path = path
        self._lock = asyncio.Lock()

        try:
            data = json_lib.read_path(self._path)
            self.collected_locations = set(data["collected_locations"])
            self.uploaded_locations = set(data["uploaded_locations"])
            self.latest_message_displayed = data["latest_message_displayed"]

        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            self.collected_locations = set()
            self.uploaded_locations = set()
            self.latest_message_displayed = 0

    async def __aenter__(self) -> Self:
        await self._lock.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        new_data = {
            "collected_locations": list(self.collected_locations),
            "uploaded_locations": list(self.uploaded_locations),
            "latest_message_displayed": self.latest_message_displayed,
        }
        json_lib.write_path(self._path, new_data)
        self._lock.release()


class MultiworldClient(QObject):
    _all_data: dict[uuid.UUID, Data]
    _persist_path: Path
    _sync_task: asyncio.Task | None = None
    _remote_games: dict[uuid.UUID, MultiplayerWorldPickups]

    _last_reported_status: dict[uuid.UUID, GameConnectionStatus]
    _last_sync: ServerSyncRequest = ServerSyncRequest(worlds=frozendict({}))

    def __init__(self, network_client: QtNetworkClient, game_connection: GameConnection, persist_path: Path):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        persist_path.mkdir(parents=True, exist_ok=True)
        self._persist_path = persist_path

        self.network_client = network_client
        self.game_connection = game_connection
        self._remote_games = {}
        self._all_data = {}
        self._last_reported_status = {}
        self._pickups_lock = asyncio.Lock()

        for f in self._persist_path.glob("*.json"):
            try:
                uid = uuid.UUID(f.name)
            except ValueError:
                self.logger.warning("File name is not an UUID: %s", f)
                continue
            self._all_data[uid] = Data(f)

        self.game_connection.GameStateUpdated.connect(self.on_game_state_updated)
        self.network_client.WorldPickupsUpdated.connect(self.on_network_game_updated)

    async def start(self):
        self.logger.debug("start")

        self.start_server_sync_task()

    async def stop(self):
        self.logger.debug("stop")

        if self._sync_task is not None:
            self._sync_task.cancel()
            self._sync_task = None

    def _locations_to_upload(self, uid: uuid.UUID) -> tuple[int, ...]:
        data = self._get_data_for(uid)
        return tuple(i for i in sorted(data.collected_locations)
                     if i not in data.uploaded_locations)

    def _create_new_sync_request(self) -> ServerSyncRequest:
        sync_requests = {}

        for state in self.game_connection.connected_states.values():
            sync_requests[state.id] = ServerWorldSync(
                status=state.status,
                collected_locations=self._locations_to_upload(state.id),
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
        for uid, data in self._all_data.items():
            if uid not in sync_requests and (locations := self._locations_to_upload(uid)):
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
                    collected_locations=self._locations_to_upload(uid),
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

            for uid, world in request.worlds.items():
                if uid in result.errors:
                    continue

                self._last_reported_status[uid] = world.status
                if world.collected_locations:
                    async with self._get_data_for(uid) as data_mod:
                        data_mod.uploaded_locations.update(world.collected_locations)

            # for uid, world in result.worlds.items():
            #     # TODO: store world name/session somewhere

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

            # Wait a bit, and try sending a new request in case new data came while waiting for the server response
            await asyncio.sleep(4)

    def start_server_sync_task(self):
        if self._sync_task is not None and not self._sync_task.done():
            return

        self._sync_task = asyncio.create_task(self._server_sync())

    def _get_data_for(self, uid: uuid.UUID) -> Data:
        if uid not in self._all_data:
            self._all_data[uid] = Data(self._persist_path.joinpath(f"{uid}.json"))

        return self._all_data[uid]

    @asyncSlot(ConnectedGameState)
    async def on_game_state_updated(self, state: ConnectedGameState):
        data = self._get_data_for(state.id)
        our_indices: set[int] = {i.index for i in state.collected_indices}
        if new_indices := our_indices - data.collected_locations:
            async with data as data_edit:
                data_edit.collected_locations.update(new_indices)

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
