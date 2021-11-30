import json
import os
from pathlib import Path
from typing import Optional, List, Union

import open_dread_rando

from randovania.game_description import default_database
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node import Node
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches
from randovania.games.game import RandovaniaGame
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import status_update_lib
from randovania.patching.patcher import Patcher


def _get_item_id_for_item(item: ItemResourceInfo) -> str:
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

        inventory = {
            "ITEM_MAX_LIFE": 99,
            "ITEM_MAX_SPECIAL_ENERGY": 1000,
            "ITEM_WEAPON_MISSILE_MAX": 15,
            "ITEM_WEAPON_POWER_BOMB_MAX": 0,
            "ITEM_METROID_COUNT": 0,
            "ITEM_METROID_TOTAL_COUNT": 40,
            "ITEM_FLOOR_SLIDE": 1,
        }
        for resource, quantity in patches.starting_items.items():
            try:
                inventory[_get_item_id_for_item(resource)] = quantity
            except KeyError:
                print(f"Skipping {resource}")
                continue

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

        return {
            "starting_location": _start_point_ref_for(_node_for(patches.starting_location)),
            "starting_items": inventory,
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
