import uuid
from PySide6.QtCore import Signal

from randovania.game_connection.connector.remote_connector import RemoteConnector, PickupEntryWithOwner
from randovania.games.game import RandovaniaGame


class DebugRemoteConnector(RemoteConnector):
    remote_pickups: tuple[PickupEntryWithOwner, ...] = tuple()
    _finished: bool = False

    RemotePickupsUpdated = Signal()

    def __init__(self, game: RandovaniaGame):
        super().__init__()
        self._game = game
        self._layout_uuid = uuid.UUID("00000000-0000-1111-0000-000000000000")

    @property
    def game_enum(self) -> RandovaniaGame:
        return self._game

    def description(self) -> str:
        return f"{self.game_enum.long_name}"

    async def set_remote_pickups(self, remote_pickups: tuple[PickupEntryWithOwner, ...]):
        self.remote_pickups = remote_pickups
        self.RemotePickupsUpdated.emit()

    async def force_finish(self):
        self._finished = True
        self.Finished.emit()

    def is_disconnected(self) -> bool:
        return self._finished

