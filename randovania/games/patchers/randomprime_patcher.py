import copy
import json
import os
import typing
from pathlib import Path
from random import Random
from typing import Optional, List, Union

import py_randomprime

import randovania
from randovania.dol_patching import assembler
from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.world.node import PickupNode, TeleporterNode
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.games.patcher import Patcher
from randovania.games.prime import prime1_elevators, all_prime_dol_patches, prime_items
from randovania.games.prime.patcher_file_lib import pickup_exporter, item_names, guaranteed_item_hint, hint_lib, \
    credits_spoiler
from randovania.generator.item_pool import pickup_creator
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.prime1.prime_configuration import PrimeConfiguration, LayoutCutsceneMode
from randovania.layout.prime1.prime_cosmetic_patches import PrimeCosmeticPatches
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
    "combatVisor": 17,
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

_MODEL_MAPPING = {
    (RandovaniaGame.METROID_PRIME_ECHOES, "ChargeBeam INCOMPLETE"): "Charge Beam",
    (RandovaniaGame.METROID_PRIME_ECHOES, "SuperMissile"): "Super Missile",
    (RandovaniaGame.METROID_PRIME_ECHOES, "ScanVisor INCOMPLETE"): "Scan Visor",
    (RandovaniaGame.METROID_PRIME_ECHOES, "VariaSuit INCOMPLETE"): "Varia Suit",
    (RandovaniaGame.METROID_PRIME_ECHOES, "DarkSuit"): "Varia Suit",
    (RandovaniaGame.METROID_PRIME_ECHOES, "LightSuit"): "Varia Suit",
    (RandovaniaGame.METROID_PRIME_ECHOES, "MorphBall INCOMPLETE"): "Morph Ball",
    (RandovaniaGame.METROID_PRIME_ECHOES, "MorphBallBomb"): "Morph Ball Bomb",
    (RandovaniaGame.METROID_PRIME_ECHOES, "BoostBall"): "Boost Ball",
    (RandovaniaGame.METROID_PRIME_ECHOES, "SpiderBall"): "Spider Ball",
    (RandovaniaGame.METROID_PRIME_ECHOES, "PowerBomb"): "Power Bomb",
    (RandovaniaGame.METROID_PRIME_ECHOES, "PowerBombExpansion"): "Power Bomb Expansion",
    (RandovaniaGame.METROID_PRIME_ECHOES, "MissileExpansion"): "Missile",
    (RandovaniaGame.METROID_PRIME_ECHOES, "MissileExpansionPrime1"): "Missile",
    (RandovaniaGame.METROID_PRIME_ECHOES, "MissileLauncher"): "Missile",
    (RandovaniaGame.METROID_PRIME_ECHOES, "GrappleBeam"): "Grapple Beam",
    (RandovaniaGame.METROID_PRIME_ECHOES, "SpaceJumpBoots"): "Space Jump Boots",
    (RandovaniaGame.METROID_PRIME_ECHOES, "EnergyTank"): "Energy Tank",
}


def prime1_pickup_details_to_patcher(detail: pickup_exporter.ExportedPickupDetails) -> dict:
    if detail.model.game == RandovaniaGame.METROID_PRIME:
        model_name = detail.model.name
    else:
        model_name = _MODEL_MAPPING.get((detail.model.game, detail.model.name), "Nothing")

    pickup_type = "Nothing"
    count = 0

    for resource, quantity in detail.conditional_resources[0].resources:
        if resource.index >= 1000:
            continue
        pickup_type = resource.long_name
        count = quantity
        break

    scan_text = detail.scan_text
    hud_text = detail.hud_text[0]

    return {
        "type": pickup_type,
        "model": model_name,
        "scanText": scan_text,
        "hudmemoText": hud_text,
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
    def export_can_be_aborted(self) -> bool:
        """
        Checks if patch_game can be aborted
        """
        return False

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
        return "Prime Randomizer - {}".format(seed_hash)

    @property
    def valid_input_file_types(self) -> List[str]:
        return ["iso"]

    @property
    def valid_output_file_types(self) -> List[str]:
        return ["iso", "ciso", "gcz"]

    def create_patch_data(self, description: LayoutDescription, players_config: PlayersConfiguration,
                          cosmetic_patches: PrimeCosmeticPatches):
        patches = description.all_patches[players_config.player_index]
        db = default_database.game_description_for(RandovaniaGame.METROID_PRIME)
        preset = description.permalink.get_preset(players_config.player_index)
        configuration = typing.cast(PrimeConfiguration, preset.configuration)
        rng = Random(description.permalink.seed_number)

        area_namers = {
            index: hint_lib.AreaNamer(default_database.game_description_for(player_preset.game).world_list)
            for index, player_preset in description.permalink.presets.items()
        }

        scan_visor = db.resource_database.get_item_by_name("Scan Visor")
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
            if world.name == "End of Game":
                continue

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

        if cosmetic_patches.open_map and configuration.elevators.is_vanilla:
            map_default_state = "visible"
        else:
            map_default_state = "default"

        credits_string = credits_spoiler.prime_trilogy_credits(
            configuration.major_items_configuration,
            description.all_patches,
            players_config,
            area_namers,
            "&push;&font=C29C51F1;&main-color=#89D6FF;Major Item Locations&pop;",
            "&push;&font=C29C51F1;&main-color=#33ffd6;{}&pop;",
        )

        artifacts = [
            db.resource_database.get_item(index)
            for index in prime_items.ARTIFACT_ITEMS
        ]
        resulting_hints = guaranteed_item_hint.create_guaranteed_hints_for_resources(
            description.all_patches, players_config, area_namers, False,
            [db.resource_database.get_item(index) for index in prime_items.ARTIFACT_ITEMS],
            hint_lib.TextColor.PRIME1_ITEM,
            hint_lib.TextColor.PRIME1_LOCATION,
        )

        # Tweaks
        ctwk_config = {}
        if configuration.small_samus:
            ctwk_config["playerSize"] = 0.3
            ctwk_config["morphBallSize"] = 0.3
            ctwk_config["easyLavaEscape"] = True

        return {
            "seed": description.permalink.seed_number,
            "preferences": {
                "qolGameBreaking": configuration.qol_game_breaking,
                "qolCosmetic": cosmetic_patches.qol_cosmetic,
                "qolMinorCutscenes": configuration.qol_cutscenes != LayoutCutsceneMode.ORIGINAL,
                "qolMajorCutscenes": configuration.qol_cutscenes == LayoutCutsceneMode.MAJOR,

                "obfuscateItems": False,
                "mapDefaultState": map_default_state,
                "artifactHintBehavior": None,
                "automaticCrashScreen": True,
                "trilogyDiscPath": None,
                "quickplay": False,
                "quiet": False,
            },
            "gameConfig": {
                "startingRoom": _name_for_location(db.world_list, patches.starting_location),
                "startingMemo": starting_memo,
                "warpToStart": configuration.warp_to_start,

                "nonvariaHeatDamage": configuration.heat_protection_only_varia,
                "staggeredSuitDamage": configuration.progressive_damage_reduction,
                "heatDamagePerSec": configuration.heat_damage,
                "autoEnabledElevators": patches.starting_items.get(scan_visor, 0) == 0,
                "multiworldDolPatches": True,

                "startingItems": {
                    name: _starting_items_value_for(db.resource_database, patches.starting_items, index)
                    for name, index in _STARTING_ITEM_NAME_TO_INDEX.items()
                },

                "etankCapacity": configuration.energy_per_tank,
                "itemMaxCapacity": {
                    "Unknown Item 1": db.resource_database.multiworld_magic_item.max_capacity,
                },

                "mainPlazaDoor": configuration.main_plaza_door,
                "backwardsFrigate": configuration.backwards_frigate,
                "backwardsLabs": configuration.backwards_labs,
                "backwardsUpperMines": configuration.backwards_upper_mines,
                "backwardsLowerMines": configuration.backwards_lower_mines,
                "phazonEliteWithoutDynamo": configuration.phazon_elite_without_dynamo,

                "gameBanner": {
                    "gameName": "Metroid Prime: Randomizer",
                    "gameNameFull": "Metroid Prime: Randomizer - {}".format(description.shareable_hash),
                    "description": "Seed Hash: {}".format(description.shareable_word_hash),
                },
                "mainMenuMessage": "Randovania v{}\n{}".format(randovania.VERSION, description.shareable_word_hash),

                "creditsString": credits_string,
                "artifactHints": {
                    artifact.long_name: text
                    for artifact, text in resulting_hints.items()
                },
                "artifactTempleLayerOverrides": {
                    artifact.long_name: patches.starting_items.get(artifact, 0) == 0
                    for artifact in artifacts
                },
            },
            "tweaks": ctwk_config,
            "levelData": world_data,
            "hasSpoiler": description.permalink.spoiler,
        }

    def patch_game(self, input_file: Optional[Path], output_file: Path, patch_data: dict,
                   internal_copies_path: Path, progress_update: ProgressUpdateCallable):
        if input_file is None:
            raise ValueError("Missing input file")

        symbols = py_randomprime.symbols_for_file(input_file)

        new_config = copy.copy(patch_data)
        has_spoiler = new_config.pop("hasSpoiler")
        new_config["inputIso"] = os.fspath(input_file)
        new_config["outputIso"] = os.fspath(output_file)
        new_config["gameConfig"]["updateHintStateReplacement"] = list(
            assembler.assemble_instructions(
                symbols["UpdateHintState__13CStateManagerFf"],
                [
                    *all_prime_dol_patches.remote_execution_patch_start(),
                    *all_prime_dol_patches.remote_execution_patch_end(),
                ],
                symbols=symbols)
        )

        patch_as_str = json.dumps(new_config, indent=4, separators=(',', ': '))
        if has_spoiler:
            output_file.with_name(f"{output_file.stem}-patcher.json").write_text(patch_as_str)

        os.environ["RUST_BACKTRACE"] = "1"

        py_randomprime.patch_iso_raw(
            patch_as_str,
            py_randomprime.ProgressNotifier(lambda percent, msg: progress_update(msg, percent)),
        )
