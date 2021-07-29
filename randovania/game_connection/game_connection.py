import copy
from typing import List, Any, Tuple, Optional

from PySide2.QtCore import QTimer, Signal, QObject
from qasync import asyncSlot

from randovania.game_connection.connection_backend import ConnectionBackend
from randovania.game_connection.connection_base import LocationListener
from randovania.game_connection.executor.memory_operation import MemoryOperationExecutor
from randovania.game_description.resources.pickup_entry import PickupEntry


class GameConnection(QObject, ConnectionBackend):
    Updated = Signal()

    _dt: float = 2.5
    _last_status: Any = None
    _permanent_pickups: List[Tuple[str, PickupEntry]]

    def __init__(self, executor: MemoryOperationExecutor):
        super().__init__()
        ConnectionBackend.__init__(self, executor)
        self._permanent_pickups = []

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._auto_update)
        self._timer.setInterval(self._dt * 1000)
        self._timer.setSingleShot(True)
        self._notify_status()

    def set_executor(self, executor: MemoryOperationExecutor):
        self.executor = executor
        self._notify_status()

    async def start(self):
        self._timer.start()

    async def stop(self):
        self._timer.stop()

    @asyncSlot()
    async def _auto_update(self):
        try:
            await self.update(self._dt)
            self._notify_status()
        finally:
            self._timer.start()

    def _notify_status(self):
        new_status = self.current_status
        inventory = self.get_current_inventory()

        if self._last_status != (new_status, self.executor, inventory):
            self._last_status = (new_status, self.executor, copy.copy(inventory))
            self.Updated.emit()

    @property
    def pretty_current_status(self) -> str:
        return f"{self.backend_choice.pretty_text}: {self.current_status.pretty_text}"

    @property
    def current_game_name(self) -> Optional[str]:
        if self.connector is not None:
            return self.connector.game_enum.long_name

    @property
    def name(self) -> str:
        raise ValueError("bleh")

    def set_location_collected_listener(self, listener: Optional[LocationListener]):
        super(ConnectionBackend, self).set_location_collected_listener(listener)
        self.checking_for_collected_index = listener is not None

