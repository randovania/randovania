import asyncio
import json
import logging
from pathlib import Path
from typing import AsyncContextManager

import pid
from PySide6.QtCore import QObject, Signal
from qasync import asyncSlot

from randovania.game_connection.game_connection import GameConnection
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
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

    async def __aenter__(self) -> "Data":
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
    _data: Data | None = None
    _expected_game: RandovaniaGame = None
    _notify_task: asyncio.Task | None = None
    _pid: pid.PidFile | None = None
    PendingUploadCount = Signal(int)

    def __init__(self, network_client: QtNetworkClient, game_connection: GameConnection):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.network_client = network_client
        self.game_connection = game_connection
        self._pickups_lock = asyncio.Lock()

        pid_name = game_connection.lock_identifier
        if pid_name is not None:
            self._pid = pid.PidFile(pid_name)
            try:
                self._pid.create()
            except pid.PidFileError as e:
                raise BackendInUse(Path(self._pid.filename)) from e
            self.logger.debug(f"Creating pid file at {self._pid.filename}")

    @property
    def is_active(self) -> bool:
        return self._data is not None

    async def start(self, persist_path: Path):
        self.logger.debug("start")

        if self._pid is not None and self._pid.fh is None:
            self._pid.create()

        self._data = Data(persist_path)
        self.game_connection.set_location_collected_listener(self.on_location_collected)
        self.network_client.GameSessionPickupsUpdated.connect(self.on_network_game_updated)

        self.start_notify_collect_locations_task()
        await self.network_client.game_session_request_update()

    async def stop(self):
        self.logger.debug("stop")

        if self._notify_task is not None:
            self._notify_task.cancel()
            self._notify_task = None

        self.game_connection.set_location_collected_listener(None)
        try:
            self.network_client.GameSessionPickupsUpdated.disconnect(self.on_network_game_updated)
        except RuntimeError:
            pass

        async with self._pickups_lock:
            self.game_connection.set_expected_game(None)
            self.game_connection.set_permanent_pickups(tuple())

        self._data = None
        if self._pid is not None:
            self._pid.close()

    async def _notify_collect_locations(self):
        while True:
            locations_to_upload = tuple(self._data.collected_locations - self._data.uploaded_locations)
            if not locations_to_upload:
                break

            try:
                await self.network_client.game_session_collect_locations(locations_to_upload)
            except (Exception, UnableToConnect) as e:
                message = f"Exception {type(e)} when attempting to upload {len(locations_to_upload)} locations."
                if isinstance(e, (UnableToConnect, error.NotLoggedIn, error.InvalidSession)):
                    self.logger.warning(message)
                else:
                    self.logger.exception(message)
                await asyncio.sleep(5)
                continue

            async with self._data as data:
                data.uploaded_locations.update(locations_to_upload)
            self.emit_pending_upload_count()

    def start_notify_collect_locations_task(self):
        if self._notify_task is not None and not self._notify_task.done():
            return

        self._notify_task = asyncio.create_task(self._notify_collect_locations())

    async def on_location_collected(self, game: RandovaniaGame, location: PickupIndex):
        if game != self._expected_game:
            return

        if location.index in self._data.collected_locations:
            self.logger.info(f"{location}, but location was already collected")
            return

        self.logger.info(f"{location}, a new location")
        async with self._data as data:
            data.collected_locations.add(location.index)

        self.emit_pending_upload_count()
        self.start_notify_collect_locations_task()

    @asyncSlot(GameSessionPickups)
    async def on_network_game_updated(self, pickups: GameSessionPickups):
        async with self._pickups_lock:
            self._expected_game = pickups.game
            self.game_connection.set_expected_game(pickups.game)
            self.game_connection.set_permanent_pickups(pickups.pickups)

    def num_locations_to_upload(self) -> int:
        if self._data is None:
            return 0
        return len(self._data.collected_locations - self._data.uploaded_locations)

    def emit_pending_upload_count(self):
        self.PendingUploadCount.emit(self.num_locations_to_upload())
