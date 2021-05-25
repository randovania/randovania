import contextlib
import copy
import json
import mmap
import os
import struct
import typing
from pathlib import Path
from random import Random
from typing import Optional, List, Union

import py_randomprime

import randovania
from randovania.dol_patching.assembler import ppc
from randovania.dol_patching.dol_file import DolHeader, DolEditor
from randovania.game_description import default_database
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.node import PickupNode, TeleporterNode
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.game_description.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.games.patcher import Patcher
from randovania.games.prime import prime1_elevators, all_prime_dol_patches, prime_items
from randovania.games.prime.patcher_file_lib import pickup_exporter, item_names, guaranteed_item_hint, hint_lib
from randovania.generator.item_pool import pickup_creator
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.prime1.prime_configuration import PrimeConfiguration
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


class IsoDolEditor(DolEditor):
    iso_file: typing.BinaryIO
    iso_mm: mmap.mmap
    dol_offset: int

    @classmethod
    @contextlib.contextmanager
    def open_iso(cls, output_file: Path):
        import nod
        result = nod.open_disc_from_image(os.fspath(output_file))
        if result is None:
            raise ValueError("Unable to read the recently written iso?")

        disc, _ = result
        dol_bytes = disc.get_data_partition().get_dol()
        dol_header = DolHeader.from_bytes(dol_bytes)

        with output_file.open("r+b") as out_iso:
            mm = mmap.mmap(out_iso.fileno(), 0, access=mmap.ACCESS_WRITE)
            dol_offset = mm.rfind(dol_bytes)
            if dol_offset < 0:
                raise ValueError("Unable to find dol in ISO")

            editor = IsoDolEditor(dol_header)
            editor.iso_file = out_iso
            editor.iso_mm = mm
            editor.dol_offset = dol_offset
            yield editor

    def _seek_and_read(self, seek: int, size: int):
        self.iso_mm.seek(self.dol_offset + seek)
        return self.iso_mm.read(size)

    def _seek_and_write(self, seek: int, data: bytes):
        self.iso_mm.seek(self.dol_offset + seek)
        self.iso_mm.write(data)


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

        if cosmetic_patches.open_map:
            map_default_state = "visible"
        else:
            map_default_state = "default"

        # credits_string = "&push;&font=C29C51F1;&main-color=#89D6FF;Major Item Locations&pop;",

        resulting_hints = guaranteed_item_hint.create_guaranteed_hints_for_resources(
            description.all_patches, players_config, area_namers, False,
            [db.resource_database.get_item(index) for index in prime_items.ARTIFACT_ITEMS],
        )
        artifact_hints = {
            resource.long_name.split("Artifact of ")[1]: text
            for resource, text in resulting_hints.items()
        }

        return {
            "seed": description.permalink.seed_number,
            "preferences": {
                "qolGameBreaking": configuration.qol_game_breaking,
                "qolCosmetic": cosmetic_patches.disable_hud_popup,
                "qolLogical": configuration.qol_logical,
                "qolMinorCutscenes": configuration.qol_minor_cutscenes,
                "qolMajorCutscenes": configuration.qol_major_cutscenes,

                "obfuscateItems": False,
                "mapDefaultState": map_default_state,
                "artifactHintBehavior": None,
                "trilogyDiscPath": None,
                "quickplay": False,
                "quiet": False,
            },
            "gameConfig": {
                "startingRoom": _name_for_location(db.world_list, patches.starting_location),
                "startingMemo": starting_memo,

                "nonvariaHeatDamage": configuration.heat_protection_only_varia,
                "staggeredSuitDamage": configuration.progressive_damage_reduction,
                "heatDamagePerSec": configuration.heat_damage,
                "autoEnabledElevators": patches.starting_items.get(scan_visor, 0) == 0,

                "startingItems": {
                    name: _starting_items_value_for(db.resource_database, patches.starting_items, index)
                    for name, index in _STARTING_ITEM_NAME_TO_INDEX.items()
                },

                "etankCapacity": configuration.energy_per_tank,

                "gameBanner": {
                    "gameName": "Metroid Prime: Randomizer",
                    "gameNameFull": "Metroid Prime: Randomizer - {}".format(description.shareable_hash),
                    "description": "Seed Hash: {}".format(description.shareable_word_hash),
                },
                "mainMenuMessage": "{}\n{}".format(randovania.VERSION, description.shareable_word_hash),

                "creditsString": None,
                "artifactHints": artifact_hints,
            },
            "levelData": world_data,
        }

    def patch_game(self, input_file: Optional[Path], output_file: Path, patch_data: dict,
                   game_files_path: Path, progress_update: ProgressUpdateCallable):
        if input_file is None:
            raise ValueError("Missing input file")

        db = default_database.game_description_for(RandovaniaGame.PRIME1)
        new_config = copy.copy(patch_data)
        new_config["inputIso"] = os.fspath(input_file)
        new_config["outputIso"] = os.fspath(output_file)

        patch_as_str = json.dumps(new_config, indent=4, separators=(',', ': '))
        Path("patcher.json").write_text(patch_as_str)

        py_randomprime.patch_iso_raw(
            patch_as_str,
            py_randomprime.ProgressNotifier(lambda percent, msg: progress_update(msg, percent)),
        )

        magic_item = db.resource_database.multiworld_magic_item

        with IsoDolEditor.open_iso(output_file) as dol_editor:
            dol_editor = typing.cast(IsoDolEditor, dol_editor)
            dol_editor.symbols = py_randomprime.rust.get_mp1_symbols("0-00")

            # Change the max capacity
            dol_editor.write(0x803cd6c0 + magic_item.index * 4,
                             struct.pack(">L", magic_item.max_capacity))

            # Apply remote execution patch
            dol_editor.write_instructions(
                "UpdateHintState__13CStateManagerFf",
                [
                    *all_prime_dol_patches.remote_execution_patch_start(),
                    *all_prime_dol_patches.remote_execution_patch_end(),
                ]
            )

            # IncrPickUp's switch array for UnknownItem1 to actually give stuff
            dol_editor.write(0x803DAD94, struct.pack(">L", 0x80091c54))

            # Remove DecrPickUp checks for the correct item types
            dol_editor.write_instructions(
                ("DecrPickUp__12CPlayerStateFQ212CPlayerState9EItemTypei", 5 * 4),
                [ppc.nop()] * 7,
            )
