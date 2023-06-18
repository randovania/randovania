import typing
import uuid

from PySide6 import QtCore

from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.db.area import Area
from randovania.game_description.db.region import Region
from randovania.games.game import RandovaniaGame

PickupEntryWithOwner = tuple[str, PickupEntry]


class PlayerLocationEvent(typing.NamedTuple):
    world: Region | None
    area: Area | None


class RemoteConnector(QtCore.QObject):
    _layout_uuid: uuid.UUID

    PlayerLocationChanged = QtCore.Signal(PlayerLocationEvent)
    PickupIndexCollected = QtCore.Signal(PickupIndex)
    InventoryUpdated = QtCore.Signal(dict)
    Finished = QtCore.Signal()

    @property
    def game_enum(self) -> RandovaniaGame:
        raise NotImplementedError()

    def description(self) -> str:
        raise NotImplementedError()

    @property
    def layout_uuid(self) -> uuid.UUID:
        return self._layout_uuid

    async def set_remote_pickups(self, remote_pickups: tuple[PickupEntryWithOwner, ...]):
        """
        Sets the list of remote pickups that must be sent to the game.
        :param remote_pickups: Ordered list of pickups sent from other players, with the name of the player.
        """
        raise NotImplementedError()

    async def force_finish(self):
        """Disconnect from the game, releasing any resources."""
        raise NotImplementedError()

    def is_disconnected(self) -> bool:
        """When True, this connector has lost connection with the game and must be discarded."""
        raise NotImplementedError()
