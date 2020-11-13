from enum import Enum
from typing import Optional, Callable, Awaitable, List, NamedTuple, Dict

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry


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


class ConnectionBase:
    _location_collected_listener: Optional[Callable[[int], Awaitable[None]]] = None
    _tracking_inventory: bool = True
    _displaying_messages: bool = True

    @property
    def current_status(self) -> GameConnectionStatus:
        raise NotImplementedError()

    def display_message(self, message: str):
        raise NotImplementedError()

    def get_current_inventory(self) -> Dict[ItemResourceInfo, InventoryItem]:
        raise NotImplementedError()

    def send_pickup(self, pickup: PickupEntry):
        raise NotImplementedError()

    def set_permanent_pickups(self, pickups: List[PickupEntry]):
        raise NotImplementedError()

    def set_location_collected_listener(self, listener: Optional[Callable[[int], Awaitable[None]]]):
        self._location_collected_listener = listener

    async def _emit_location_collected(self, location: int):
        if self._location_collected_listener is not None:
            await self._location_collected_listener(location)

    @property
    def tracking_inventory(self) -> bool:
        return self._tracking_inventory

    @property
    def displaying_messages(self) -> bool:
        return self._displaying_messages
