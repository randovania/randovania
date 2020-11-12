from typing import List, Dict, Optional, Any

from PySide2.QtCore import QTimer, Signal, QObject
from asyncqt import asyncSlot

from randovania.game_connection.connection_backend import ConnectionBackend
from randovania.game_connection.connection_base import GameConnectionStatus, ConnectionBase, InventoryItem
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry


class GameConnection(QObject, ConnectionBase):
    Updated = Signal()

    _dt: float = 2.5
    _last_status: Any = None
    backend: ConnectionBackend
    _permanent_pickups: List[PickupEntry]

    def __init__(self, backend: ConnectionBackend):
        super().__init__()
        self._permanent_pickups = []

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.setInterval(self._dt * 1000)
        self._timer.setSingleShot(True)

        self.set_backend(backend)

    def set_backend(self, backend: ConnectionBackend):
        if hasattr(self, "backend"):
            self.backend.set_location_collected_listener(None)
        self.backend = backend
        self.backend.set_location_collected_listener(self._emit_location_collected)
        self.backend.checking_for_collected_index = self._location_collected_listener is not None
        self.backend.set_permanent_pickups(self._permanent_pickups)
        self.backend.tracking_inventory = self.tracking_inventory
        self.backend.displaying_messages = self.displaying_messages
        self._notify_status()

    async def start(self):
        self._timer.start()

    async def stop(self):
        self._timer.stop()

    @asyncSlot()
    async def _update(self):
        try:
            await self.backend.update(self._dt)
            self._notify_status()
        finally:
            self._timer.start()

    def _notify_status(self):
        new_status = self.current_status
        if self._last_status != (new_status, self.backend):
            self._last_status = (new_status, self.backend)
            self.Updated.emit()

    @property
    def pretty_current_status(self) -> str:
        return f"{self.backend.name}: {self.backend.current_status.pretty_text}"

    @property
    def current_status(self) -> GameConnectionStatus:
        return self.backend.current_status

    def display_message(self, message: str):
        return self.backend.display_message(message)

    def get_current_inventory(self) -> Dict[ItemResourceInfo, InventoryItem]:
        return self.backend.get_current_inventory()

    def send_pickup(self, pickup: PickupEntry):
        return self.backend.send_pickup(pickup)

    def set_permanent_pickups(self, pickups: List[PickupEntry]):
        self._permanent_pickups = pickups
        return self.backend.set_permanent_pickups(pickups)

    def set_location_collected_listener(self, listener):
        super().set_location_collected_listener(listener)
        self.backend.checking_for_collected_index = listener is not None

    async def _emit_location_collected(self, location: int):
        if self._location_collected_listener is not None:
            await self._location_collected_listener(location)
        else:
            self.display_message("Pickup not sent, Randovania is not connected to a session.")

    @ConnectionBase.tracking_inventory.setter
    def tracking_inventory(self, value: bool):
        self._tracking_inventory = value
        self.backend.tracking_inventory = value

    @ConnectionBase.displaying_messages.setter
    def displaying_messages(self, value: bool):
        self._displaying_messages = value
        self.backend.displaying_messages = value
