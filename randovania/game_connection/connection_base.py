from enum import Enum
from typing import Callable, Awaitable, NamedTuple

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame


class GameConnectionStatus(Enum):
    Disconnected = "disconnected"
    UnknownGame = "unknown-game"
    WrongGame = "wrong-game"
    WrongHash = "wrong-hash"
    TitleScreen = "title-screen"
    TrackerOnly = "tracker-only"
    InGame = "in-game"

    @property
    def pretty_text(self) -> str:
        return _pretty_connection_status[self]


_pretty_connection_status = {
    GameConnectionStatus.Disconnected: "Disconnected",
    GameConnectionStatus.UnknownGame: "Unknown game",
    GameConnectionStatus.WrongGame: "Wrong game",
    GameConnectionStatus.WrongHash: "Correct game, wrong seed hash",
    GameConnectionStatus.TitleScreen: "Title screen",
    GameConnectionStatus.TrackerOnly: "Tracker only",
    GameConnectionStatus.InGame: "In-game",
}


class InventoryItem(NamedTuple):
    amount: int
    capacity: int


Inventory = dict[ItemResourceInfo, InventoryItem]
LocationListener = Callable[[RandovaniaGame, PickupIndex], Awaitable[None]]


class ConnectionBase:
    _location_collected_listener: LocationListener | None = None

    @property
    def current_status(self) -> GameConnectionStatus:
        raise NotImplementedError()

    def get_current_inventory(self) -> Inventory:
        raise NotImplementedError()

    def set_permanent_pickups(self, pickups: list[tuple[str, PickupEntry]]):
        raise NotImplementedError()

    def set_location_collected_listener(self, listener: LocationListener | None):
        self._location_collected_listener = listener

    async def _emit_location_collected(self, game: RandovaniaGame, location: PickupIndex):
        if self._location_collected_listener is not None:
            await self._location_collected_listener(game, location)
