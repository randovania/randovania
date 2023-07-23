from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter import pickup_exporter
from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.game_description.assignment import PickupTarget
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pickup_creator

if TYPE_CHECKING:
    from randovania.exporter.pickup_exporter import ExportedPickupDetails
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_info import ResourceCollection


def get_item_id_for_item(item: ItemResourceInfo) -> str:
    if "item_capacity_id" in item.extra:
        return item.extra["item_capacity_id"]
    try:
        return item.extra["item_id"]
    except KeyError as e:
        raise KeyError(f"{item.long_name} has no item ID.") from e


class MSRPatchDataFactory(BasePatchDataFactory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memo_data = MSRAcquiredMemo.with_expansion_text()

        tank = self.configuration.energy_per_tank
        self.memo_data["Energy Tank"] = f"Energy Tank acquired.\nEnergy capacity increased by {tank:g}."

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_SAMUS_RETURNS

    def _calculate_starting_inventory(self, resources: ResourceCollection):
        result = {}
        for resource, quantity in resources.as_resource_gain():
            try:
                result[get_item_id_for_item(resource)] = quantity
            except KeyError:
                print(f"Skipping {resource} for starting inventory: no item id")
                continue
        return result

    def _start_point_ref_for(self, node: Node) -> dict:
        region = self.game.region_list.nodes_to_region(node)
        level_name: str = region.extra["scenario_id"]

        if "start_point_actor_name" in node.extra:
            return {
                "scenario": level_name,
                "actor": node.extra["start_point_actor_name"],
            }
        else:
            return {}

    def _pickup_detail_for_target(self, detail: ExportedPickupDetails) -> dict | None:

        pickup_node = self.game.region_list.node_from_pickup_index(detail.index)
        pickup_type = pickup_node.extra.get("pickup_type", "actor")

        hud_text = detail.collection_text[0]
        if len(set(detail.collection_text)) > 1:
            hud_text = self.memo_data[detail.original_pickup.name]

        details = {
            "pickup_type": pickup_type,
            "caption": hud_text,
        }

        return details

    def _node_for(self, identifier:  NodeIdentifier) -> Node:
        return self.game.region_list.node_by_identifier(identifier)

    def create_data(self) -> dict:
        starting_location = self._start_point_ref_for(self._node_for(self.patches.starting_location))
        starting_items = self._calculate_starting_inventory(self.patches.starting_resources())

        useless_target = PickupTarget(pickup_creator.create_nothing_pickup(self.game.resource_database),
                                      self.players_config.player_index)

        pickup_list = pickup_exporter.export_all_indices(
            self.patches,
            useless_target,
            self.game.region_list,
            self.rng,
            self.configuration.pickup_model_style,
            self.configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(self.memo_data, self.players_config, self.game_enum()),
            visual_etm=pickup_creator.create_visual_etm(),
        )

        energy_per_tank = self.configuration.energy_per_tank

        return {
            "starting_location": starting_location,
            "starting_items": starting_items,
            "pickups": [
                data
                for pickup_item in pickup_list
                if (data := self._pickup_detail_for_target(pickup_item)) is not None
            ],
            "energy_per_tank": energy_per_tank,
        }


class MSRAcquiredMemo(dict):
    def __missing__(self, key):
        return f"{key} acquired."

    @classmethod
    def with_expansion_text(cls):
        result = cls()
        result["Missile Tank"] = "Missile Tank acquired.\nMissile capacity increased by {Missile}."
        result["Super Missile Tank"] = (
            "Super Missile Tank acquired.\n"
            "Super Missile capacity increased by {Super Missile}."
        )
        result["Power Bomb Tank"] = "Power Bomb Tank acquired.\nPower Bomb capacity increased by {Power Bomb}."
        result["Energy Tank"] = "Energy Tank acquired.\nEnergy capacity increased by 100."
        result["Aeion Tank"] = "Aeion Tank acquired.\nAieon capacity increased by {Aeion}"
        return result
