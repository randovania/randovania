from typing import List

from PySide2.QtCore import QTimer, Signal, QObject
from asyncqt import asyncSlot

from randovania.game_connection.connection_backend import ConnectionBackend, ConnectionBase, ConnectionStatus
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import CurrentResources


class GameConnection(QObject, ConnectionBase):
    StatusUpdated = Signal(ConnectionStatus)

    _dt: float = 1.0
    _current_status: ConnectionStatus = ConnectionStatus.Disconnected
    backend: ConnectionBackend = None

    def __init__(self):
        super().__init__()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.setInterval(self._dt * 1000)

    def set_backend(self, backend: ConnectionBackend):
        if self.backend is not None:
            self.backend.set_location_collected_listener(None)

        self.backend = backend
        self.backend.set_location_collected_listener(self._emit_location_collected)

    async def start(self):
        self._timer.start()

    async def stop(self):
        self._timer.stop()

    @asyncSlot()
    async def _update(self):
        await self.backend.update(self._dt)
        new_status = self.backend.current_status
        if self._current_status != new_status:
            self._current_status = new_status
            self.StatusUpdated.emit(new_status)

    @property
    def pretty_current_status(self) -> str:
        return f"{self.backend.name}: {self.backend.current_status.pretty_text}"

    @property
    def current_status(self) -> ConnectionStatus:
        return self.backend.current_status

    def display_message(self, message: str):
        return self.backend.display_message(message)

    async def get_inventory(self) -> CurrentResources:
        return await self.backend.get_inventory()

    def send_pickup(self, pickup: PickupEntry):
        return self.backend.send_pickup(pickup)

    def set_permanent_pickups(self, pickups: List[PickupEntry]):
        return self.backend.set_permanent_pickups(pickups)

    async def _emit_location_collected(self, location: int):
        if self._location_collected_listener is not None:
            await self._location_collected_listener(location)
        else:
            self.backend.display_message("Pickup not sent, Randovania is not connected to a session.")
