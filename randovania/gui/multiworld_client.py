import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import AsyncContextManager, Self

from PySide6.QtCore import QObject, Signal
from qasync import asyncSlot

from randovania.game_connection.connector.remote_connector import RemoteConnector
from randovania.game_connection.game_connection import GameConnection, ConnectedGameState
from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.network_client.game_session import GameSessionPickups
from randovania.network_client.network_client import UnableToConnect
from randovania.network_common import error


class BackendInUse(Exception):
    def __init__(self, lock_file: Path):
        self.lock_file = lock_file


class Data(AsyncContextManager):
    collected_locations: set[int]
    uploaded_locations: set[int]
    latest_message_displayed: int

    def __init__(self, path: Path):
        self._path = path
        self._lock = asyncio.Lock()

        try:
            with self._path.open() as f:
                data = json.load(f)
            self.collected_locations = set(data["collected_locations"])
            self.uploaded_locations = set(data["uploaded_locations"])
            self.latest_message_displayed = data["latest_message_displayed"]
        except FileNotFoundError:
            self.collected_locations = set()
            self.uploaded_locations = set()
            self.latest_message_displayed = 0

    async def __aenter__(self) -> Self:
        await self._lock.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        new_data = json.dumps({
            "collected_locations": list(self.collected_locations),
            "uploaded_locations": list(self.uploaded_locations),
            "latest_message_displayed": self.latest_message_displayed,
        })
        self._path.write_text(new_data)
        self._lock.release()


class MultiworldClient(QObject):
    _all_data: dict[uuid.UUID, Data] | None = None
    _persist_path: Path
    _notify_task: asyncio.Task | None = None
    _remote_games: dict[uuid.UUID, GameSessionPickups]
    PendingUploadCount = Signal(int)

    def __init__(self, network_client: QtNetworkClient, game_connection: GameConnection):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.network_client = network_client
        self.game_connection = game_connection
        self._remote_games = {}
        self._pickups_lock = asyncio.Lock()

    @property
    def is_active(self) -> bool:
        return self._all_data is not None

    async def start(self, persist_path: Path):
        self.logger.debug("start")

        persist_path.mkdir(parents=True, exist_ok=True)
        self._persist_path = persist_path
        self._all_data = {}
        self.game_connection.GameStateUpdated.connect(self.on_game_state_updated)
        self.network_client.GameSessionPickupsUpdated.connect(self.on_network_game_updated)

        self.start_notify_collect_locations_task()
        await self.network_client.game_session_request_update()

    async def stop(self):
        self.logger.debug("stop")

        if self._notify_task is not None:
            self._notify_task.cancel()
            self._notify_task = None

        try:
            self.game_connection.GameStateUpdated.disconnect(self.on_game_state_updated)
        except RuntimeError:
            pass

        try:
            self.network_client.GameSessionPickupsUpdated.disconnect(self.on_network_game_updated)
        except RuntimeError:
            pass

        self._remote_games = {}
        self._all_data = None

    async def _notify_collect_locations(self):
        keep_alive = True
        while keep_alive:
            keep_alive = False
            for data in self._all_data.values():
                locations_to_upload = tuple(data.collected_locations - data.uploaded_locations)
                if not locations_to_upload:
                    continue

                keep_alive = True

                try:
                    await self.network_client.game_session_collect_locations(locations_to_upload)
                except (Exception, UnableToConnect) as e:
                    message = f"Exception {type(e)} when attempting to upload {len(locations_to_upload)} locations."
                    if isinstance(e, (UnableToConnect, error.NotLoggedIn, error.InvalidSession, error.RequestTimeout)):
                        self.logger.warning(message)
                    else:
                        self.logger.exception(message)
                    await asyncio.sleep(5)
                    continue

                async with data as data_mod:
                    data_mod.uploaded_locations.update(locations_to_upload)
                self.emit_pending_upload_count()

    def start_notify_collect_locations_task(self):
        if self._notify_task is not None and not self._notify_task.done():
            return

        self._notify_task = asyncio.create_task(self._notify_collect_locations())

    async def _on_new_state(self):
        if self._all_data is None:
            return

        connector_by_uid: dict[uuid.UUID, RemoteConnector] = {
            state.id: connector
            for connector, state in self.game_connection.connected_states.items()
        }

        for uid, remote_game in self._remote_games.items():
            if uid not in self._all_data:
                self._all_data[uid] = Data(self._persist_path.joinpath(f"{uid}.json"))

            data = self._all_data[uid]
            connector = connector_by_uid.get(uid)
            state = self.game_connection.connected_states.get(connector)

            if state is not None:
                await connector.set_remote_pickups(remote_game.pickups)

                our_indices: set[int] = {i.index for i in state.collected_indices}
                new_indices = our_indices - data.collected_locations
                if new_indices:
                    async with data as data_edit:
                        data_edit.collected_locations.update(new_indices)
                    self.emit_pending_upload_count()
                    self.start_notify_collect_locations_task()

    @asyncSlot(ConnectedGameState)
    async def on_game_state_updated(self, state: ConnectedGameState):
        await self._on_new_state()

    @asyncSlot(GameSessionPickups)
    async def on_network_game_updated(self, pickups: GameSessionPickups):
        async with self._pickups_lock:
            self._remote_games[pickups.id] = pickups
        await self._on_new_state()

    def num_locations_to_upload(self) -> int:
        for data in (self._all_data or {}).values():
            return len(data.collected_locations - data.uploaded_locations)
        return 0

    def emit_pending_upload_count(self):
        self.PendingUploadCount.emit(self.num_locations_to_upload())
