import json
import logging
import os
from pathlib import Path
from random import Random
from typing import Optional, List, Union

import open_dread_rando

from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import ConditionalResources
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
        item_db = default_database.item_database_for_game(RandovaniaGame.METROID_DREAD)
        configuration = description.get_preset(players_config.player_index).configuration
        assert isinstance(configuration, DreadConfiguration)
        rng = Random(description.get_seed_for_player(players_config.player_index))

        def _calculate_starting_inventory(resources: CurrentResources):
            result = {}
            for resource, quantity in resources.items():
                try:
                    result[_get_item_id_for_item(resource)] = quantity
                except KeyError:
                    print(f"Skipping {resource} for starting inventory: no item id")
                    continue
            return result

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

        def _level_name_for(node: Node) -> str:
            world = db.world_list.nodes_to_world(node)
            return os.path.splitext(os.path.split(world.extra["asset_id"])[1])[0]

        def _teleporter_ref_for(node: Node) -> dict:
            try:
                return {
                    "scenario": _level_name_for(node),
                    "layer": node.extra.get("actor_layer", "default"),
                    "actor": node.extra["actor_name"],
                }
            except KeyError as e:
                raise KeyError(f"{node} has no extra {e}")
        
        def _callback_ref_for(node: Node) -> dict:
            try:
                return {
                    "scenario": _level_name_for(node),
                    "function": node.extra["callback_function"],
                    "args": node.extra.get("callback_args", 0)
                }
            except KeyError as e:
                raise KeyError(f"{node} has no extra {e}")

        def _pickup_detail_for_target(detail: ExportedPickupDetails) -> Optional[dict]:
            # target.

            if detail.model.game != RandovaniaGame.METROID_DREAD:
                model_name = "itemsphere"
            else:
                model_name = detail.model.name
            
            ammoconfig = configuration.ammo_configuration.items_state
            pbammo = item_db.ammo["Power Bomb Expansion"]

            def get_resource(res: ConditionalResources) -> dict:
                item_id = "ITEM_NONE"
                quantity = 1
                ids = [_get_item_id_for_item(r) for r, q in res.resources]
                for r, q in res.resources:
                    try:
                        item_id = _get_item_id_for_item(r)
                        quantity = q
                        break
                    except KeyError:
                        continue
                
                if "ITEM_WEAPON_POWER_BOMB" in ids:
                    item_id = "ITEM_WEAPON_POWER_BOMB"
                
                # non-required mains
                if (item_id == "ITEM_WEAPON_POWER_BOMB_MAX"
                    and not ammoconfig[pbammo].requires_major_item):
                    item_id = "ITEM_WEAPON_POWER_BOMB"

                return {"item_id": item_id, "quantity": quantity}
            
            # ugly hack
            resources = [get_resource(res) for res in detail.conditional_resources]
            if resources[0]["item_id"] == "ITEM_WEAPON_POWER_BOMB_MAX":
                resources = [resources[-1]]

            pickup_node = db.world_list.node_from_pickup_index(detail.index)
            pickup_type = pickup_node.extra.get("pickup_type", "actor")

            hud_text = detail.hud_text[0]
            if len(detail.hud_text) > 1:
                hud_text = DreadAcquiredMemo()[detail.original_pickup.name]

            details = {
                "pickup_type": pickup_type,
                "caption": hud_text,
                "resources": resources
            }

            try:
                if pickup_type == "actor":
                    details.update({
                        "pickup_actor": _teleporter_ref_for(pickup_node),
                        "model": model_name,
                    })
                else:
                    details.update({
                        "pickup_actordef": pickup_node.extra["actor_def"],
                        "pickup_string_key": pickup_node.extra["string_key"],
                        "pickup_lua_callback": _callback_ref_for(pickup_node),
                    })
                return details
            except KeyError as e:
                logging.warn(e)
                return None

        starting_location = _start_point_ref_for(_node_for(patches.starting_location))
        starting_items = _calculate_starting_inventory(patches.starting_items)

        useless_target = PickupTarget(pickup_creator.create_nothing_pickup(db.resource_database),
                                      players_config.player_index)

        pickup_list = pickup_exporter.export_all_indices(
            patches,
            useless_target,
            db.world_list,
            rng,
            configuration.pickup_model_style,
            configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(db, DreadAcquiredMemo(), players_config),
            visual_etm=pickup_creator.create_visual_etm(),
        )

        return {
            "starting_location": starting_location,
            "starting_items": starting_items,
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

class DreadAcquiredMemo(dict):
    def __missing__(self, key):
        return "{} acquired.".format(key)