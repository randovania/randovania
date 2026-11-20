from __future__ import annotations

import json
from typing import TYPE_CHECKING, override

from randovania.game.game_enum import RandovaniaGame
from randovania.game_connection.connector.mercury_remote_connector import MercuryConnector
from randovania.game_connection.executor.yoku_executor import lua_string
from randovania.game_description import default_database
from randovania.game_description.resources.inventory import Inventory, InventoryItem

if TYPE_CHECKING:
    from randovania.game_connection.executor.yoku_executor import YokuExecutor
    from randovania.game_description.pickup.pickup_entry import ConditionalResources, PickupEntry
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo


class YokuRemoteConnector(MercuryConnector):
    _game_enum: RandovaniaGame = RandovaniaGame.YOKUS_ISLAND_EXPRESS

    def __init__(self, executor: YokuExecutor):
        super().__init__(executor, self._game_enum)
        self._progressions = self._progressive_stages()

    def description(self) -> str:
        return self.game_enum.long_name

    def _progressive_stages(self) -> list[list[ItemResourceInfo]]:
        resource_db = self.game.get_resource_database_view()
        pickup_db = default_database.pickup_database_for_game(self._game_enum)
        return [
            [resource_db.get_item(name) for name in pickup.progression]
            for pickup in pickup_db.standard_pickups.values()
            if len(pickup.progression) > 1
        ]

    @override
    def new_inventory_received(self, json_string: str) -> None:
        try:
            inventory_json = json.loads(json_string)
            self.inventory_index = inventory_json["index"]
            counts: list[int] = [round(count) for count in inventory_json["inventory"]]
        except Exception as e:
            self.logger.error("Unknown response: %s (got %s)", json_string, e)
            return

        items = [r for r in self.game.get_resource_database_view().get_all_items() if "item_id" in r.extra]
        quantities = dict(zip(items, counts))

        # Handle that the game drops a stage when its upgrade arrives
        for stages in self._progressions:
            highest = max((i for i, stage in enumerate(stages) if quantities.get(stage, 0) > 0), default=0)
            for stage in stages[:highest]:
                quantities[stage] = max(quantities.get(stage, 0), 1)

        inventory = Inventory({item: InventoryItem(quantity, quantity) for item, quantity in quantities.items()})
        self.last_inventory = inventory
        self.InventoryUpdated.emit(inventory)

    @override
    async def receive_remote_pickups(self) -> None:
        if self.received_pickups is None or self.inventory_index is None:
            return

        num_pickups = self.received_pickups
        if num_pickups >= len(self.remote_pickups) or self.in_cooldown:
            return

        self.in_cooldown = True

        provider_name, pickup, _ = self.remote_pickups[num_pickups]
        item_name = self._item_name(pickup)
        progression = self._game_item_progression(pickup)
        message = self.format_received_item(item_name, provider_name)
        self.logger.info(
            "%d permanent pickups, received %d. Next pickup: %s", len(self.remote_pickups), num_pickups, message
        )

        await self.executor.run_lua_code(
            f"RL.GiveItem({lua_string(progression)},{lua_string(message)},{num_pickups},{self.inventory_index})"
        )

    def _item_name(self, pickup: PickupEntry) -> str:
        resources = self.game.get_resource_database_view().create_resource_collection()
        resources.add_resource_gain(self.last_inventory.as_resource_gain())
        conditional = pickup.conditional_for_resources(resources)
        return conditional.name if conditional.name is not None else pickup.name

    def _game_item_progression(self, pickup: PickupEntry) -> str:
        """Every stage's game item id from the lowest up, as `RL.GiveItem` takes it; the game picks the stage."""
        stages = [resource.extra["item_id"] for resource, _ in pickup.progression if "item_id" in resource.extra]
        if not stages:
            stages = [pickup.extra["item_id"]]
        return ",".join(stages)

    def get_resources_for_details(
        self, pickup: PickupEntry, conditional_resources: list[ConditionalResources], other_player: bool
    ) -> list:
        raise NotImplementedError("Yoku gives remote pickups by item id")

    async def display_arbitrary_message(self, message: str) -> None:
        await self.executor.run_lua_code(f"RL.ShowMessage({lua_string(message)})")
