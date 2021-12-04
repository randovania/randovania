import json
import os
from pathlib import Path
from random import Random
from typing import Optional, List, Union

import open_dread_rando

from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node import Node
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches
from randovania.games.game import RandovaniaGame
from randovania.generator.item_pool import pickup_creator
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import status_update_lib
from randovania.patching.patcher import Patcher
from randovania.patching.prime.patcher_file_lib import pickup_exporter
from randovania.patching.prime.patcher_file_lib.pickup_exporter import ExportedPickupDetails


def _get_item_id_for_item(item: ItemResourceInfo) -> str:
    if "item_capacity_id" in item.extra:
        return item.extra["item_capacity_id"]
    return item.extra["item_id"]


class OpenDreadPatcher(Patcher):
    _busy: bool = False

    @property
    def is_busy(self) -> bool:
        """
        Checks if the patcher is busy right now
        """
        return self._busy

    @property
    def export_can_be_aborted(self) -> bool:
        """
        Checks if patch_game can be aborted
        """
        return True

    @property
    def uses_input_file_directly(self) -> bool:
        """
        Does this patcher uses the input file directly?
        """
        return True

    def has_internal_copy(self, internal_copies_path: Path) -> bool:
        return False

    def delete_internal_copy(self, internal_copies_path: Path):
        pass

    def default_output_file(self, seed_hash: str) -> str:
        return "Dread Randomizer - {}".format(seed_hash)

    @property
    def valid_input_file_types(self) -> List[str]:
        return [""]

    @property
    def valid_output_file_types(self) -> List[str]:
        return [""]

    def create_patch_data(self, description: LayoutDescription, players_config: PlayersConfiguration,
                          cosmetic_patches: DreadCosmeticPatches):
        patches = description.all_patches[players_config.player_index]
        db = default_database.game_description_for(RandovaniaGame.METROID_DREAD)
        configuration = description.permalink.get_preset(players_config.player_index).configuration
        assert isinstance(configuration, DreadConfiguration)
        rng = Random(description.permalink.seed_number)

        inventory = {
            "ITEM_MAX_LIFE": 99,
            "ITEM_MAX_SPECIAL_ENERGY": 1000,
            "ITEM_METROID_COUNT": 0,
            "ITEM_METROID_TOTAL_COUNT": 40,
            "ITEM_WEAPON_MISSILE_MAX": 0,
            "ITEM_WEAPON_POWER_BOMB_MAX": 0,
        }

        # ITEM_MAX_LIFE = 99
        # ITEM_MAX_SPECIAL_ENERGY = 1000
        # ITEM_METROID_COUNT = 0
        # ITEM_METROID_TOTAL_COUNT = 40
        # ITEM_WEAPON_MISSILE_MAX = 15
        # ITEM_WEAPON_POWER_BOMB_MAX = 0
        # ITEM_FLOOR_SLIDE = 1

        def _fill_inventory(resources: CurrentResources):
            for resource, quantity in resources.items():
                try:
                    inventory[_get_item_id_for_item(resource)] = quantity
                except KeyError:
                    print(f"Skipping {resource}")
                    continue

        _fill_inventory(patches.starting_items)

        def _node_for(identifier: Union[AreaIdentifier, NodeIdentifier]) -> Node:
            if isinstance(identifier, NodeIdentifier):
                return db.world_list.node_by_identifier(identifier)
            else:
                area = db.world_list.area_by_area_location(identifier)
                node = area.node_with_name(area.default_node)
                assert node is not None
                return node

        def _start_point_ref_for(node: Node) -> dict:
            world = db.world_list.nodes_to_world(node)
            level_name: str = os.path.splitext(os.path.split(world.extra["asset_id"])[1])[0]

            try:
                return {
                    "scenario": level_name,
                    "actor": node.extra["start_point_actor_name"],
                }
            except KeyError as e:
                raise KeyError(f"{node} has no extra {e}")

        def _teleporter_ref_for(node: Node) -> dict:
            world = db.world_list.nodes_to_world(node)
            level_name: str = os.path.splitext(os.path.split(world.extra["asset_id"])[1])[0]

            try:
                return {
                    "scenario": level_name,
                    "layer": node.extra.get("actor_layer", "default"),
                    "actor": node.extra["actor_name"],
                }
            except KeyError as e:
                raise KeyError(f"{node} has no extra {e}")

        def _pickup_detail_for_target(detail: ExportedPickupDetails) -> Optional[dict]:
            # target.

            if detail.model.game != RandovaniaGame.METROID_DREAD:
                model_name = "itemsphere"
            else:
                model_name = detail.model.name

            item_id = "ITEM_NONE"
            quantity = 1
            for r, q in detail.conditional_resources[0].resources:
                try:
                    item_id = _get_item_id_for_item(r)
                    quantity = q
                    break
                except KeyError:
                    continue

            if item_id is None:
                raise ValueError(f"Missing item id: {detail.hud_text}")

            try:
                return {
                    "pickup_actor": _teleporter_ref_for(db.world_list.node_from_pickup_index(detail.index)),
                    "caption": "\n".join(detail.hud_text),
                    "item_id": item_id,
                    "quantity": quantity,
                    "model": model_name,
                }
            except KeyError:
                return None

        useless_target = PickupTarget(pickup_creator.create_nothing_pickup(db.resource_database),
                                      players_config.player_index)

        pickup_list = pickup_exporter.export_all_indices(
            patches,
            useless_target,
            db.world_list,
            rng,
            configuration.pickup_model_style,
            configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(db, pickup_exporter.GenericAcquiredMemo(), players_config),
            visual_etm=pickup_creator.create_visual_etm(),
        )

        return {
            "starting_location": _start_point_ref_for(_node_for(patches.starting_location)),
            "starting_items": inventory,
            "pickups": [
                data
                for pickup_item in pickup_list
                if (data := _pickup_detail_for_target(pickup_item)) is not None
            ],
            "elevators": [
                {
                    "teleporter": _teleporter_ref_for(_node_for(source)),
                    "destination": _start_point_ref_for(_node_for(target)),
                }
                for source, target in patches.elevator_connection.items()
            ]
        }

    def patch_game(self, input_file: Optional[Path], output_file: Path, patch_data: dict,
                   internal_copies_path: Path, progress_update: status_update_lib.ProgressUpdateCallable):

        output_file.mkdir(parents=True, exist_ok=True)
        with output_file.joinpath("patcher.json").open("w") as f:
            json.dump(patch_data, f, indent=4)
        open_dread_rando.patch(input_file, output_file, patch_data)
