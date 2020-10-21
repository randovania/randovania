from typing import List, Dict, Callable, Awaitable, Optional

from _nod import Enum

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


_pretty_connection_status: Dict[ConnectionStatus, str] = {
    ConnectionStatus.Disconnected: "Disconnected",
    ConnectionStatus.WrongGame: "Wrong Game",
    ConnectionStatus.WrongHash: "Correct Game, Wrong Seed Hash",
    ConnectionStatus.TitleScreen: "Title Screen",
    ConnectionStatus.TrackerOnly: "Tracker Only",
    ConnectionStatus.InGame: "In-Game",
}


class ConnectionBase:
    _location_collected_listener: Optional[Callable[[int], Awaitable[None]]] = None

    @property
    def current_status(self) -> ConnectionStatus:
        raise NotImplementedError()

    def display_message(self, message: str):
        raise NotImplementedError()

    async def get_inventory(self) -> CurrentResources:
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


class ConnectionBackend(ConnectionBase):
    _checking_for_collected_index: bool = False

    @property
    def name(self) -> str:
        raise NotImplementedError()

    async def update(self, dt: float):
        raise NotImplementedError()

    @property
    def lock_identifier(self) -> Optional[str]:
        raise NotImplementedError()

    @property
    def checking_for_collected_index(self):
        return self._checking_for_collected_index

    @checking_for_collected_index.setter
    def checking_for_collected_index(self, value):
        self._checking_for_collected_index = value
