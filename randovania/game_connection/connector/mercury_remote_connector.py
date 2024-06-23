from __future__ import annotations

import json
import logging
import typing
import uuid
from typing import TYPE_CHECKING

from qasync import asyncSlot  # type: ignore

from randovania.exporter.pickup_exporter import _conditional_resources_for_pickup
from randovania.game_connection.connector.remote_connector import (
    PickupEntryWithOwner,
    PlayerLocationEvent,
    RemoteConnector,
)
from randovania.game_description import default_database
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_collection import ResourceCollection

if TYPE_CHECKING:
    from randovania.game_description.db.region import Region
    from randovania.game_description.pickup.pickup_entry import ConditionalResources, PickupEntry
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.games.game import RandovaniaGame


class MercuryConnector(RemoteConnector):
    last_inventory: Inventory

    def __init__(self, executor: typing.Any, game_enum: RandovaniaGame):
        super().__init__()
        self._layout_uuid = uuid.UUID(executor.layout_uuid_str)
        self.logger = logging.getLogger(type(self).__name__)
        self.executor = executor
        self.game = default_database.game_description_for(game_enum)
        self._game_enum = game_enum

        self.reset_values()

        self.executor.signals.new_inventory.connect(self.new_inventory_received)
        self.executor.signals.new_collected_locations.connect(self.new_collected_locations_received)
        self.executor.signals.new_player_location.connect(self.new_player_location_received)
        self.executor.signals.new_received_pickups.connect(self.new_received_pickups_received)
        self.executor.signals.connection_lost.connect(self.connection_lost)

    @property
    def game_enum(self) -> RandovaniaGame:
        return self._game_enum

    async def current_game_status(self) -> tuple[bool, Region | None]:
        return (self.in_cooldown, self.current_region)

    def connection_lost(self) -> None:
        self.logger.info("Finishing connector")

    async def force_finish(self) -> None:
        self.executor.disconnect()

    def is_disconnected(self) -> bool:
        return not self.executor.is_connected()

    # reset all values on init, disconnect or after switching back to main menu
    def reset_values(self) -> None:
        self.remote_pickups: tuple[PickupEntryWithOwner, ...] = ()
        self.last_inventory = Inventory.empty()
        self.in_cooldown = True
        self.received_pickups: int | None = None
        self.inventory_index: int | None = None
        self.current_region: Region | None = None

    def new_player_location_received(self, state_or_region: str) -> None:
        if state_or_region == "MAINMENU":
            self.reset_values()
            self.current_region = None
        else:
            self.current_region = next(
                (region for region in self.game.region_list.regions if region.extra["scenario_id"] == state_or_region),
                None,
            )
        self.PlayerLocationChanged.emit(PlayerLocationEvent(self.current_region, None))

    def new_collected_locations_received(self, new_indices: bytes) -> None:
        locations = set()
        start_of_bytes = b"locations:"
        if new_indices.startswith(start_of_bytes):
            index = 0
            for c in new_indices[len(start_of_bytes) :]:
                for i in range(8):
                    if c & (1 << i):
                        locations.add(PickupIndex(index))
                    index += 1
        else:
            self.logger.warning("Unknown response: %s", new_indices)

        for location in locations:
            self.PickupIndexCollected.emit(location)

    def new_inventory_received(self, json_string: str) -> None:
        try:
            inventory_json = json.loads(json_string)
            self.inventory_index = inventory_json["index"]
            inventory_ints: list[int] = inventory_json["inventory"]
        except Exception as e:
            self.logger.error("Unknown response: %s (got %s)", json_string, e)
            return

        items = [r for r in self.game.resource_database.item if "item_id" in r.extra]

        inventory = Inventory(
            {item: InventoryItem(quantity, quantity) for item, quantity in zip(items, inventory_ints)}
        )
        self.last_inventory = inventory
        self.InventoryUpdated.emit(inventory)

    @asyncSlot()
    async def new_received_pickups_received(self, new_received_pickups: str) -> None:
        new_recv_as_int = int(new_received_pickups)
        self.logger.debug("Received Pickups: %s", new_received_pickups)
        self.in_cooldown = False
        self.received_pickups = new_recv_as_int
        await self.receive_remote_pickups()

    async def set_remote_pickups(self, remote_pickups: tuple[PickupEntryWithOwner, ...]) -> None:
        self.remote_pickups = remote_pickups
        await self.receive_remote_pickups()

    async def receive_remote_pickups(self) -> None:
        remote_pickups = self.remote_pickups
        inventory = self.last_inventory

        # in that case we never received the numbers (at least 0) from the game
        if self.received_pickups is None or self.inventory_index is None:
            return

        num_pickups = self.received_pickups

        if num_pickups >= len(remote_pickups) or self.in_cooldown:
            return

        self.in_cooldown = True

        provider_name, pickup = remote_pickups[num_pickups]
        item_name, items_list = self.resources_to_give_for_pickup(self.game.resource_database, pickup, inventory)

        self.logger.debug("Resource changes for %s from %s", pickup.name, provider_name)

        await self.game_specific_execute(item_name, items_list, provider_name)

    async def game_specific_execute(self, item_name: str, items_list: list, provider_name: str) -> None:
        raise NotImplementedError

    async def display_arbitrary_message(self, message: str) -> None:
        raise NotImplementedError

    def format_received_item(self, item_name: str, player_name: str) -> str:
        generic = "Received {item_name} from {provider_name}."
        return generic.format(item_name=item_name, provider_name=player_name)

    def get_resources_for_details(
        self, pickup: PickupEntry, conditional_resources: list[ConditionalResources], other_player: bool
    ) -> list:
        raise NotImplementedError

    def resources_to_give_for_pickup(
        self,
        db: ResourceDatabase,
        pickup: PickupEntry,
        inventory: Inventory,
    ) -> tuple[str, list[list[dict]]]:
        inventory_resources = ResourceCollection.with_database(db)
        inventory_resources.add_resource_gain(inventory.as_resource_gain())
        conditional = pickup.conditional_for_resources(inventory_resources)
        if conditional.name is not None:
            item_name = conditional.name
        else:
            item_name = pickup.name

        conditional_resources = _conditional_resources_for_pickup(pickup)
        resources = self.get_resources_for_details(pickup, conditional_resources, False)

        return item_name, resources
