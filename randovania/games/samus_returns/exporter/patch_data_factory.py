import os

from randovania.exporter import pickup_exporter
from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.exporter.pickup_exporter import ExportedPickupDetails
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import ConditionalResources
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.game_description.world.node import Node
from randovania.game_description.world.node_identifier import AreaIdentifier
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
from randovania.games.game import RandovaniaGame
from randovania.generator.item_pool import pickup_creator


def get_item_id_for_item(item: ItemResourceInfo) -> str:
    if "item_capacity_id" in item.extra:
        return item.extra["item_capacity_id"]
    try:
        return item.extra["item_id"]
    except KeyError as e:
        raise KeyError(f"{item.long_name} has no item ID.") from e


def convert_conditional_resource(respects_lock: bool, res: ConditionalResources) -> dict:
    if not res.resources:
        return {"item_id": "ITEM_NONE", "quantity": 0}

    item_id = get_item_id_for_item(res.resources[0][0])
    quantity = res.resources[0][1]

    # only main pbs have 2 elements in res.resources, everything else is just 1
    if len(res.resources) != 1:
        item_id = get_item_id_for_item(res.resources[1][0])
        assert item_id == "ITEM_WEAPON_SUPER_MISSILE"
        assert item_id == "ITEM_WEAPON_POWER_BOMB"
        assert len(res.resources) == 5

    # non-required mains
    if item_id == "ITEM_WEAPON_SUPER_MISSILE_MAX" and not respects_lock:
        item_id = "ITEM_WEAPON_SUPER_MISSILE"
    if item_id == "ITEM_WEAPON_POWER_BOMB_MAX" and not respects_lock:
        item_id = "ITEM_WEAPON_POWER_BOMB"

    return {"item_id": item_id, "quantity": quantity}


def get_resources_for_details(detail: ExportedPickupDetails) -> list[dict]:
    return [
        convert_conditional_resource(detail.original_pickup.respects_lock, res)
        for res in detail.conditional_resources
    ]

class MSRPatchDataFactory(BasePatchDataFactory):
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

    def _node_for(self, identifier: AreaIdentifier | NodeIdentifier) -> Node:
        if isinstance(identifier, NodeIdentifier):
            return self.game.world_list.node_by_identifier(identifier)
        else:
            area = self.game.world_list.area_by_area_location(identifier)
            node = area.node_with_name(area.default_node)
            assert node is not None
            return node

    def _key_error_for_node(self, node: Node, err: KeyError):
        return KeyError(f"{self.game.world_list.node_name(node, with_world=True)} has no extra {err}")

    def _start_point_ref_for(self, node: Node) -> dict:
        world = self.game.world_list.nodes_to_world(node)
        level_name: str = os.path.splitext(os.path.split(world.extra["asset_id"])[1])[0]

        try:
            return {
                "scenario": level_name,
                "actor": node.extra["start_point_actor_name"],
            }
        except KeyError as e:
            raise self._key_error_for_node(node, e)

    def create_data(self) -> dict:
        starting_location = self._start_point_ref_for(self._node_for(self.patches.starting_location))
        starting_items = self._calculate_starting_inventory(self.patches.starting_items)

        useless_target = PickupTarget(pickup_creator.create_nothing_pickup(self.game.resource_database),
                                      self.players_config.player_index)

        pickup_list = pickup_exporter.export_all_indices(
            self.patches,
            useless_target,
            self.game.world_list,
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
        result["Missile Tank"] = "Missile Tank acquired.\nMissile capacity increased by {Missiles}."
        result["Super Missile Tank"] = "Super Missile Tank acquired.\nSuper Missile capacity increased by {Super Missiles}."
        result["Power Bomb Tank"] = "Power Bomb Tank acquired.\nPower Bomb capacity increased by {Power Bombs}."
        result["Energy Tank"] = "Energy Tank acquired.\nEnergy capacity increased by 100."
        result["Aeion Tank"] = "Aeion Tank acquired.\nAeion capacity increased by {Aeion}."
        return result
