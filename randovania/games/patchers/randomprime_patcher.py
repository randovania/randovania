import copy
import json
import os
from pathlib import Path
from random import Random
from typing import Optional, List, Union

import py_randomprime
import typing

from randovania.game_description import default_database
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.node import PickupNode, TeleporterNode
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.game_description.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.games.patcher import Patcher
from randovania.games.prime import prime1_elevators
from randovania.games.prime.patcher_file_lib import pickup_exporter, item_names
from randovania.generator.item_pool import pickup_creator
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.prime_configuration import PrimeConfiguration
from randovania.lib.status_update_lib import ProgressUpdateCallable

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


def prime1_pickup_details_to_patcher(detail: pickup_exporter.ExportedPickupDetails) -> dict:
    if detail.model.game == RandovaniaGame.PRIME1:
        model_name = detail.model.name
    else:
        model_name = "Nothing"

    pickup_type = "Nothing"
    count = 0

    for resource, quantity in detail.conditional_resources[0].resources:
        if resource.index >= 1000:
            continue
        pickup_type = resource.long_name
        count = quantity
        break

    return {
        "type": pickup_type,
        "model": model_name,
        "scanText": detail.scan_text,
        "hudmemoText": detail.hud_text[0],
        "count": count,
        "respawn": False
    }


def _starting_items_value_for(resource_database: ResourceDatabase,
                              starting_items: CurrentResources, index: int) -> Union[bool, int]:
    item = resource_database.get_item(index)
    value = starting_items.get(item, 0)
    if item.max_capacity > 1:
        return value
    else:
        return value > 0


def _name_for_location(world_list: WorldList, location: AreaLocation) -> str:
    if location in prime1_elevators.CUSTOM_NAMES:
        return prime1_elevators.CUSTOM_NAMES[location]
    else:
        return world_list.area_name(world_list.area_by_area_location(location), separator=":")


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
        preset = description.permalink.get_preset(players_config.player_index)
        configuration = typing.cast(PrimeConfiguration, preset.configuration)
        rng = Random(description.permalink.seed_number)

        useless_target = PickupTarget(pickup_creator.create_prime1_useless_pickup(db.resource_database),
                                      players_config.player_index)

        pickup_list = pickup_exporter.export_all_indices(
            patches,
            useless_target,
            db.world_list.num_pickup_nodes,
            rng,
            configuration.pickup_model_style,
            configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(db, pickup_exporter.GenericAcquiredMemo(), players_config),
            visual_etm=pickup_creator.create_visual_etm(),
        )
        world_data = {}
        for world in db.world_list.worlds:
            world_data[world.name] = {
                "transports": {},
                "rooms": {}
            }
            for area in world.areas:
                pickup_indices = sorted(node.pickup_index for node in area.nodes if isinstance(node, PickupNode))
                if pickup_indices:
                    world_data[world.name]["rooms"][area.name] = {
                        "pickups": [
                            prime1_pickup_details_to_patcher(pickup_list[index.index])
                            for index in pickup_indices
                        ],
                    }

                for node in area.nodes:
                    if not isinstance(node, TeleporterNode) or not node.editable:
                        continue

                    target = _name_for_location(db.world_list, patches.elevator_connection[node.teleporter])
                    source_name = prime1_elevators.CUSTOM_NAMES[node.teleporter.area_location]
                    world_data[world.name]["transports"][source_name] = target

        starting_memo = None
        extra_starting = item_names.additional_starting_items(configuration, db.resource_database,
                                                              patches.starting_items)
        if extra_starting:
            starting_memo = ", ".join(extra_starting)

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
                "startingRoom": _name_for_location(db.world_list, patches.starting_location),
                "startingMemo": starting_memo,

                "nonvariaHeatDamage": True,
                "staggered_suit_damage": True,
                "autoEnabledElevators": False,

                "startingItems": {
                    name: _starting_items_value_for(db.resource_database, patches.starting_items, index)
                    for name, index in _STARTING_ITEM_NAME_TO_INDEX.items()
                },

                "etankCapacity": configuration.energy_per_tank,
                "mainMenuMessage": description.shareable_word_hash,

                "gameBanner": {
                    "gameName": "Metroid Prime: Randomizer",
                    "gameNameFull": "Metroid Prime: Randomizer - {}".format(description.shareable_hash),
                },
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
        Path("patcher.json").write_text(patch_as_str)

        py_randomprime.patch_iso_raw(
            patch_as_str,
            py_randomprime.ProgressNotifier(lambda percent, msg: progress_update(msg, percent)),
        )
