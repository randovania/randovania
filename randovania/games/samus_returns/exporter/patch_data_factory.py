import os
from typing import Iterator

from randovania.exporter import pickup_exporter, item_names
from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.exporter.pickup_exporter import ExportedPickupDetails
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import ConditionalResources
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.node import Node
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
from randovania.games.samus_returns.layout.msr_cosmetic_patches import MSRCosmeticPatches
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pickup_creator


def get_item_id_for_item(item: ItemResourceInfo) -> str:
    if "item_capacity_id" in item.extra:
        return item.extra["item_capacity_id"]
    try:
        return item.extra["item_id"]
    except KeyError as e:
        raise KeyError(f"{item.long_name} has no item ID.") from e


def convert_conditional_resource(res: ConditionalResources) -> Iterator[dict]:
    if not res.resources:
        yield {"item_id": "ITEM_NONE", "quantity": 0}
        return

    for resource in reversed(res.resources):
        item_id = get_item_id_for_item(resource[0])
        quantity = resource[1]

        yield {"item_id": item_id, "quantity": quantity}



def get_resources_for_details(detail: ExportedPickupDetails) -> list[list[dict]]:
    pickup = detail.original_pickup
    resources = [
        list(convert_conditional_resource(conditional_resource))
        for conditional_resource in detail.conditional_resources
    ]

    if pickup.resource_lock is not None and not pickup.respects_lock and not pickup.unlocks_resource:
        # Add the lock resource into the pickup in addition to the expansion's resources
        assert len(resources) == 1
        resources[0].append({
            "item_id": get_item_id_for_item(pickup.resource_lock.locked_by),
            "quantity": 1,
        })

    return resources

class MSRPatchDataFactory(BasePatchDataFactory):
    cosmetic_patches: MSRCosmeticPatches
    configuration: MSRConfiguration

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

    def _starting_inventory_text(self):
        result = [r"{c1}Random starting items:{c0}"]
        items = item_names.additional_starting_equipment(self.configuration, self.game, self.patches)
        if not items:
            return []
        result.extend(items)
        return result

    def _node_for(self, identifier: AreaIdentifier | NodeIdentifier) -> Node:
        if isinstance(identifier, NodeIdentifier):
            return self.game.region_list.node_by_identifier(identifier)
        else:
            area = self.game.region_list.area_by_area_location(identifier)
            node = area.node_with_name(area.default_node)
            assert node is not None
            return node

    def _key_error_for_node(self, node: Node, err: KeyError):
        return KeyError(f"{self.game.region_list.node_name(node, with_region=True)} has no extra {err}")
    
    def _key_error_for_start_node(self, node: Node):
        return KeyError(f"{self.game.region_list.node_name(node, with_region=True)} has neither a " +
                        "start_point_actor_name nor the area has a collision_camera_name for a custom start point")

    def _start_point_ref_for(self, node: Node) -> dict:
        region = self.game.region_list.nodes_to_region(node)
        level_name: str = os.path.splitext(os.path.split(region.extra["asset_id"])[1])[0]

        try:
            return {
                "scenario": level_name,
                "actor": node.extra["start_point_actor_name"],
            }
        except KeyError as e:
            raise self._key_error_for_node(node, e)

    def _pickup_detail_for_target(self, detail: ExportedPickupDetails) -> dict | None:
        # target.

        resources = get_resources_for_details(detail)

        pickup_node = self.game.region_list.node_from_pickup_index(detail.index)
        pickup_type = pickup_node.extra.get("pickup_type", "actor")

        hud_text = detail.collection_text[0]
        if len(set(detail.collection_text)) > 1:
            hud_text = self.memo_data[detail.original_pickup.name]

        details = {
            "pickup_type": pickup_type,
            "caption": hud_text,
            "resources": resources,
        }

        return details

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
            exporter=pickup_exporter.create_pickup_exporter(self.game, self.memo_data, self.players_config),
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
            "Super Missile Tank acquired."
            "\nSuper Missile capacity increased by {Super Missile}."
        )
        result["Power Bomb Tank"] = "Power Bomb Tank acquired.\nPower Bomb capacity increased by {Power Bomb}."
        result["Energy Tank"] = "Energy Tank acquired.\nEnergy capacity increased by 100."
        result["Aeion Tank"] = "Aeion Tank acquired.\nAeion capacity increased by {Aeion}."
        return result
