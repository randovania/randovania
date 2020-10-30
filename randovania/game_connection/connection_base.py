from enum import Enum
from typing import Optional, Callable, Awaitable, List, NamedTuple, Dict

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import CurrentResources


class ConnectionStatus(Enum):
    Disconnected = "disconnected"
    WrongGame = "wrong-game"
    WrongHash = "wrong-hash"
    TitleScreen = "title-screen"
    TrackerOnly = "tracker-only"
    InGame = "in-game"

    @property
    def pretty_text(self) -> str:
        return _pretty_connection_status[self]


_pretty_connection_status = {
    ConnectionStatus.Disconnected: "Disconnected",
    ConnectionStatus.WrongGame: "Wrong Game",
    ConnectionStatus.WrongHash: "Correct Game, Wrong Seed Hash",
    ConnectionStatus.TitleScreen: "Title Screen",
    ConnectionStatus.TrackerOnly: "Tracker Only",
    ConnectionStatus.InGame: "In-Game",
}


class InventoryItem(NamedTuple):
    amount: int
    capacity: int


class ConnectionBase:
    _location_collected_listener: Optional[Callable[[int], Awaitable[None]]] = None

    @property
    def current_status(self) -> ConnectionStatus:
        raise NotImplementedError()

    def display_message(self, message: str):
        raise NotImplementedError()

    async def get_inventory(self) -> Dict[ItemResourceInfo, InventoryItem]:
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
