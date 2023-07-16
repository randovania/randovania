from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal

from randovania.game_connection.connector.remote_connector import PickupEntryWithOwner, RemoteConnector

if TYPE_CHECKING:
    import uuid

    from randovania.games.game import RandovaniaGame


class DebugRemoteConnector(RemoteConnector):
    remote_pickups: tuple[PickupEntryWithOwner, ...] = ()
    _finished: bool = False

    RemotePickupsUpdated = Signal()

    def __init__(self, game: RandovaniaGame, layout_uuid: uuid.UUID):
        super().__init__()
        self._game = game
        self._layout_uuid = layout_uuid

    @property
    def game_enum(self) -> RandovaniaGame:
        return self._game

    def description(self) -> str:
        return f"{self.game_enum.long_name}: {self._layout_uuid}"

    async def set_remote_pickups(self, remote_pickups: tuple[PickupEntryWithOwner, ...]):
        self.remote_pickups = remote_pickups
        self.RemotePickupsUpdated.emit()

    async def force_finish(self):
        self._finished = True
        self.Finished.emit()

    def is_disconnected(self) -> bool:
        return self._finished

