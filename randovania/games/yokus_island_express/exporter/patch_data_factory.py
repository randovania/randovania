from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.games.yokus_island_express.exporter.hint_namer import YokuHintNamer
from randovania.games.yokus_island_express.layout import YokuConfiguration, YokuCosmeticPatches
from randovania.generator.pickup_pool import pickup_creator

if TYPE_CHECKING:
    from randovania.exporter.hints.hint_namer import HintNamer
    from randovania.exporter.patch_data_factory import PatcherDataMeta
    from randovania.game_description.pickup.pickup_entry import PickupEntry

NOTHING_ITEM = "nothing"

FRUIT_ITEMS = frozenset({"reward_fruit_big", "reward_fruit_medium"})
"""Never starting items: fruit is a counter in the save, and `starting_fruit` sets it."""


class YokuPatchDataFactory(PatchDataFactory[YokuConfiguration, YokuCosmeticPatches]):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.YOKUS_ISLAND_EXPRESS

    @override
    @classmethod
    def hint_namer_type(cls) -> type[HintNamer]:
        return YokuHintNamer

    @override
    def create_visual_nothing(self) -> PickupEntry:
        return pickup_creator.create_visual_nothing(self.game_enum(), NOTHING_ITEM)

    def _create_pickups(self) -> list[dict]:
        pickups = []
        for details in sorted(self.export_pickup_list(), key=lambda pickup: pickup.index):
            node = self.game.region_list.node_from_pickup_index(details.index)
            item = None if details.is_for_remote_player else details.original_pickup.extra.get("item_id")
            pickups.append(
                {
                    "location": node.extra["spawn_id"],
                    "item": item or NOTHING_ITEM,
                }
            )
        return pickups

    def _create_starting_items(self) -> dict[str, int]:
        starting_items = {}
        for resource, quantity in self.patches.starting_resources().as_resource_gain():
            if isinstance(resource, ItemResourceInfo) and quantity > 0:
                item_id = resource.extra["item_id"]
                if item_id not in FRUIT_ITEMS:
                    starting_items[item_id] = quantity

        # In the game an upgrade replaces the stage below it, so a progressive pickup starts with its highest stage only
        for pickup in self.pickup_db.standard_pickups.values():
            stages = [self.resource_db.get_item(name).extra["item_id"] for name in pickup.progression]
            held = [stage for stage in stages if stage in starting_items]
            for stage in held[:-1]:
                del starting_items[stage]

        return dict(sorted(starting_items.items()))

    def create_game_specific_data(self, randovania_meta: PatcherDataMeta) -> dict:
        return {
            "configuration_identifier": self.description.shareable_hash,
            "seed_hash": f"{self.description.shareable_word_hash} ({self.description.shareable_hash})",
            "layout_uuid": str(self.world_uuid),
            "save": {
                "seed": self.description.get_seed_for_world(self.worlds_config.world_index),
            },
            "pickups": self._create_pickups(),
            "starting_items": self._create_starting_items(),
            "starting_fruit": self.configuration.effective_starting_fruit,
            "required_beacons": self.configuration.required_beacons,
        }
