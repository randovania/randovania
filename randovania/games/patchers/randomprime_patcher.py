import copy
import json
import os
from pathlib import Path
from typing import Optional, List, Union

import py_randomprime

from randovania.game_description import default_database
from randovania.game_description.node import PickupNode
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.games.game import RandovaniaGame
from randovania.games.patcher import Patcher
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.layout.layout_description import LayoutDescription

_STARTING_ITEM_NAME_TO_INDEX = {
    "powerBeam": 0,
    "ice": 1,
    "wave": 2,
    "plasma": 3,
    "missiles": 4,
    "scanVisor": 5,
    "bombs": 6,
    "powerBombs": 7,
    "flamethrower": 8,
    "thermalVisor": 9,
    "charge": 10,
    "superMissile": 11,
    "grapple": 12,
    "xray": 13,
    "iceSpreader": 14,
    "spaceJump": 15,
    "morphBall": 16,
    "boostBall": 18,
    "spiderBall": 19,
    "gravitySuit": 21,
    "variaSuit": 22,
    "phazonSuit": 23,
    "energyTanks": 24,
    "wavebuster": 28
}


# "Power Suit": 20,
# "Combat Visor": 17,
# "Unknown Item 1": 25,
# "Health Refill": 26,
# "Unknown Item 2": 27,


def _starting_items_value_for(resource_database: ResourceDatabase,
                              starting_items: CurrentResources, index: int) -> Union[bool, int]:
    item = resource_database.get_item(index)
    value = starting_items.get(item, 0)
    if item.max_capacity > 1:
        return value
    else:
        return value > 0


class RandomprimePatcher(Patcher):
    _busy: bool = False

    @property
    def is_busy(self) -> bool:
        """
        Checks if the patcher is busy right now
        """
        return self._busy

    @property
    def uses_input_file_directly(self) -> bool:
        """
        Does this patcher uses the input file directly?
        """
        return True

    def has_internal_copy(self, game_files_path: Path) -> bool:
        return False

    def delete_internal_copy(self, game_files_path: Path):
        pass

    def default_output_file(self, seed_hash: str) -> str:
        return "Prime Randomizer - {}.iso".format(seed_hash)

    @property
    def valid_input_file_types(self) -> List[str]:
        return ["iso"]

    @property
    def valid_output_file_types(self) -> List[str]:
        return ["iso"]

    def create_patch_data(self, description: LayoutDescription, players_config: PlayersConfiguration,
                          cosmetic_patches: CosmeticPatches):
        patches = description.all_patches[players_config.player_index]
        db = default_database.game_description_for(RandovaniaGame.PRIME1)

        world_data = {}
        for world in db.world_list.worlds:
            world_data[world.name] = {
                 "transports": {},
                 "rooms": {}
            }
            for area in world.areas:
                pickup_indices = sorted(node.pickup_index for node in area.nodes if isinstance(node, PickupNode))
                if not pickup_indices:
                    continue

                pickups = []
                world_data[world.name]["rooms"][area.name] = {"pickups": pickups}
                for index in pickup_indices:
                    target = patches.pickup_assignment.get(index)

                    if target is None:
                        pickup_type = "Nothing"
                        hud_memo = "Nothing"
                        count = 0

                    else:
                        pickup_type = None
                        hud_memo = target.pickup.name
                        count = 0

                        for resource, quantity in target.pickup.progression:
                            pickup_type = resource.long_name
                            count = quantity
                            break

                        if pickup_type is None:
                            for resource, quantity in target.pickup.extra_resources:
                                pickup_type = resource.long_name
                                count = quantity
                                break

                        if pickup_type is None:
                            raise ValueError("pickup has nothing?!")

                    pickups.append({
                        "type": pickup_type,
                        "model": pickup_type,
                        "scanText": pickup_type,
                        "hudmemoText": f"{hud_memo} acquired!",
                        "count": count,
                        "respawn": False
                    })

        return {
            "seed": description.permalink.seed_number,
            "preferences": {
                "skipHudmenus": cosmetic_patches.disable_hud_popup,
                "obfuscateItems": False,
                "mapDefaultState": None,
                "artifactHintBehavior": None,
                "trilogyDiscPath": None,
                "keepFmvs": True,
                "quickplay": False,
                "quiet": False,
            },
            "gameConfig": {
                "startingRoom": "tallon:alcove",
                "startingMemo": "nice",
                "startingItems": {
                    name: _starting_items_value_for(db.resource_database, patches.starting_items, index)
                    for name, index in _STARTING_ITEM_NAME_TO_INDEX.items()
                }
            },
            "levelData": world_data,
        }

    def patch_game(self, input_file: Optional[Path], output_file: Path, patch_data: dict,
                   game_files_path: Path, progress_update: ProgressUpdateCallable):
        if input_file is None:
            raise ValueError("Missing input file")

        new_config = copy.copy(patch_data)
        new_config["inputIso"] = os.fspath(input_file)
        new_config["outputIso"] = os.fspath(output_file)

        patch_as_str = json.dumps(new_config, indent=4, separators=(',', ': '))
        print(patch_as_str)

        py_randomprime.patch_iso_raw(
            patch_as_str,
            py_randomprime.ProgressNotifier(lambda percent, msg: progress_update(msg, percent)),
        )
