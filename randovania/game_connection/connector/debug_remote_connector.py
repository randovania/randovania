from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal

from randovania.game_connection.connector.remote_connector import PickupEntryWithOwner, RemoteConnector
from randovania.game_description import default_database
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.game_description.resources.resource_collection import ResourceCollection

if TYPE_CHECKING:
    import uuid

    from randovania.games.game import RandovaniaGame


class DebugRemoteConnector(RemoteConnector):
    messages: list[str]
    remote_pickups: tuple[PickupEntryWithOwner, ...] = ()
    _finished: bool = False
    _last_inventory_event: Inventory
    item_collection: ResourceCollection

    RemotePickupsUpdated = Signal()
    MessagesUpdated = Signal()

    def __init__(self, game: RandovaniaGame, layout_uuid: uuid.UUID):
        super().__init__()
        self._game = game
        self._layout_uuid = layout_uuid
        self._last_inventory_event = Inventory({})

        self.messages = []
        self.item_collection = ResourceCollection.with_database(default_database.resource_database_for(game))
        self._last_remote_pickup = 0

    @property
    def game_enum(self) -> RandovaniaGame:
        return self._game

    def description(self) -> str:
        return f"{self.game_enum.long_name}: {self._layout_uuid}"

    async def display_arbitrary_message(self, message: str):
        self.messages.append(message)
        self.MessagesUpdated.emit()

    async def set_remote_pickups(self, remote_pickups: tuple[PickupEntryWithOwner, ...]):
        self.remote_pickups = remote_pickups

        for remote_pickup in remote_pickups[self._last_remote_pickup :]:
            self.messages.append(f"Received {remote_pickup[1].name} from {remote_pickup[0]}")
            self.item_collection.add_resource_gain(remote_pickup[1].resource_gain(self.item_collection))
            self._last_remote_pickup += 1

        self.RemotePickupsUpdated.emit()
        self.MessagesUpdated.emit()
        self.emit_inventory()

    async def force_finish(self):
        self._finished = True

    def is_disconnected(self) -> bool:
        return self._finished

    def emit_inventory(self):
        new_inventory = Inventory(
            {
                resource: InventoryItem(quantity, quantity)
                for resource, quantity in self.item_collection.as_resource_gain()
            }
        )
        if self._last_inventory_event != new_inventory:
            self._last_inventory_event = new_inventory
            self.InventoryUpdated.emit(new_inventory)
