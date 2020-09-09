from typing import List, Dict

from PySide2.QtCore import Signal, QObject
from _nod import Enum

from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import CurrentResources


class ConnectionStatus(Enum):
    Disconnected = "disconnected"
    WrongGame = "wrong-game"
    WrongHash = "wrong-hash"
    TitleScreen = "title-screen"
    InGame = "in-game"

    @property
    def pretty_text(self) -> str:
        return _pretty_connection_status[self]


_pretty_connection_status: Dict[ConnectionStatus, str] = {
    ConnectionStatus.Disconnected: "Disconnected",
    ConnectionStatus.WrongGame: "Wrong Game",
    ConnectionStatus.WrongHash: "Correct Game, Wrong Seed Hash",
    ConnectionStatus.TitleScreen: "Title Screen",
    ConnectionStatus.InGame: "In-Game",
}


class ConnectionBase(QObject):
    LocationCollected = Signal(int)

    @property
    def current_status(self) -> ConnectionStatus:
        raise NotImplementedError()

    async def display_message(self, message: str):
        raise NotImplementedError()

    async def get_inventory(self) -> CurrentResources:
        raise NotImplementedError()

    def send_pickup(self, pickup: PickupEntry):
        raise NotImplementedError()

    def set_permanent_pickups(self, pickups: List[PickupEntry]):
        raise NotImplementedError()


class ConnectionBackend(ConnectionBase):
    @property
    def name(self) -> str:
        raise NotImplementedError()

    async def update(self, dt: float):
        raise NotImplementedError()
