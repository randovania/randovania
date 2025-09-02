from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_connection.connector.remote_connector import RemoteConnector
from randovania.game_description.resources.inventory import Inventory
from randovania.lib.signal import RdvSignal

if TYPE_CHECKING:
    import uuid

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.network_common.remote_pickup import RemotePickup


class DebugRemoteConnector(RemoteConnector):
    messages: list[str]
    remote_pickups: tuple[RemotePickup, ...] = ()
    _finished: bool = False
    _last_inventory_event: Inventory
    item_collection: ResourceCollection
    RemotePickupsUpdated = RdvSignal()
    MessagesUpdated = RdvSignal()

    def __init__(self, game: RandovaniaGame, layout_uuid: uuid.UUID):
        super().__init__()
        self._game = game
        self._layout_uuid = layout_uuid
        self._last_inventory_event = Inventory({})

        self.messages = []
        self.item_collection = game.game_description.create_resource_collection()
        self._last_remote_pickup = 0

    @property
    def game_enum(self) -> RandovaniaGame:
        return self._game

    def description(self) -> str:
        return f"{self.game_enum.long_name}: {self._layout_uuid}"

    async def display_arbitrary_message(self, message: str) -> None:
        self.messages.append(message)
        self.MessagesUpdated.emit()

    async def set_remote_pickups(self, remote_pickups: tuple[RemotePickup, ...]) -> None:
        self.remote_pickups = remote_pickups

        for remote_pickup in remote_pickups[self._last_remote_pickup :]:
            self.messages.append(f"Received {remote_pickup[1].name} from {remote_pickup[0]}")
            self.item_collection.add_resource_gain(remote_pickup[1].resource_gain(self.item_collection))
            self._last_remote_pickup += 1

        self.RemotePickupsUpdated.emit()
        self.MessagesUpdated.emit()
        self.emit_inventory()

    async def force_finish(self) -> None:
        self._finished = True

    def is_disconnected(self) -> bool:
        return self._finished

    def emit_inventory(self) -> None:
        new_inventory = Inventory.from_collection(self.item_collection)
        if self._last_inventory_event != new_inventory:
            self._last_inventory_event = new_inventory
            self.InventoryUpdated.emit(new_inventory)
