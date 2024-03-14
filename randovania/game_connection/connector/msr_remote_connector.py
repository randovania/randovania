from __future__ import annotations

import json
import logging
import uuid
from typing import TYPE_CHECKING

from qasync import asyncSlot

from randovania.game_connection.connector.remote_connector import (
    PickupEntryWithOwner,
    PlayerLocationEvent,
    RemoteConnector,
)
from randovania.game_description import default_database
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame

if TYPE_CHECKING:
    from randovania.game_connection.executor.msr_executor import MSRExecutor
    from randovania.game_description.db.region import Region


class MSRRemoteConnector(RemoteConnector):
    last_inventory: Inventory
    _game_enum: RandovaniaGame = RandovaniaGame.METROID_SAMUS_RETURNS

    def __init__(self, executor: MSRExecutor):
        super().__init__()
        self._layout_uuid = uuid.UUID(executor.layout_uuid_str)
        self.logger = logging.getLogger(type(self).__name__)
        self.executor = executor
        self.game = default_database.game_description_for(RandovaniaGame.METROID_SAMUS_RETURNS)

        self.reset_values()

        self.executor.signals.new_inventory.connect(self.new_inventory_received)
        self.executor.signals.new_collected_locations.connect(self.new_collected_locations_received)
        self.executor.signals.new_player_location.connect(self.new_player_location_received)
        self.executor.signals.new_received_pickups.connect(self.new_received_pickups_received)
        self.executor.signals.connection_lost.connect(self.connection_lost)

    @property
    def game_enum(self) -> RandovaniaGame:
        return self._game_enum

    def description(self) -> str:
        return f"{self.game_enum.long_name}: {self.executor.version}"

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
        self.remote_pickups = ()
        self.last_inventory = Inventory.empty()
        self.in_cooldown = True
        self.received_pickups = None
        self.inventory_index = None
        self.current_region = None

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

        self.logger.info(locations)

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
        raise NotImplementedError

    async def set_remote_pickups(self, remote_pickups: tuple[PickupEntryWithOwner, ...]) -> None:
        raise NotImplementedError

    async def receive_remote_pickups(self) -> None:
        raise NotImplementedError

    async def display_arbitrary_message(self, message: str) -> None:
        raise NotImplementedError
