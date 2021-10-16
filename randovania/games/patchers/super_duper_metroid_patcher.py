import os
import pprint
import shutil
import typing
from pathlib import Path
from random import Random
from typing import List, Optional

import SuperDuperMetroid.ROM_Patcher
import SuperDuperMetroid.SM_Constants

from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.games.game import RandovaniaGame
from randovania.games.patcher import Patcher
from randovania.games.prime.patcher_file_lib import pickup_exporter
from randovania.generator.item_pool import pickup_creator
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.super_metroid.super_metroid_configuration import SuperMetroidConfiguration
from randovania.layout.super_metroid.super_metroid_cosmetic_patches import SuperMetroidCosmeticPatches
from randovania.lib.status_update_lib import ProgressUpdateCallable


_multiplier_for_item = {
    "Energy Tank": 100, "Reserve Tank": 100,
}


def sm_pickup_details_to_patcher(detail: pickup_exporter.ExportedPickupDetails,
                                 ) -> dict:
    if detail.model.game == RandovaniaGame.SUPER_METROID:
        model_name = detail.model.name
    else:
        model_name = "Nothing"

    scan_text = detail.scan_text
    hud_text = detail.hud_text[0]
    pickup_type = "Nothing"
    count = 0

    for resource, quantity in detail.conditional_resources[0].resources:
        if resource.index >= 1000:
            continue
        pickup_type = resource.long_name
        count = quantity
        break

    count *= _multiplier_for_item.get(pickup_type, 1)

    _mapping = {
        "Missile": "Missile Expansion",
        "Super Missile": "Super Missile Expansion",
        "Power Bombs": "Power Bomb Expansion",

        "Nothing": "Missile Expansion",
    }

    result = {
        "item_name": _mapping.get(pickup_type, pickup_type),
        "quantity": count,
        "pickup_index": detail.index.index,
    }

    return result


def _json_to_pickup_placement_data(pickup: dict) -> SuperDuperMetroid.ROM_Patcher.PickupPlacementData:
    return SuperDuperMetroid.ROM_Patcher.PickupPlacementData(
        quantity_given=pickup["quantity"],
        pickup_index=pickup["pickup_index"],
        item_name=pickup["item_name"],
    )


class SuperDuperMetroidPatcher(Patcher):
    @property
    def is_busy(self) -> bool:
        """
        Checks if the patcher is busy right now
        """
        return False

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
        return False

    def has_internal_copy(self, game_files_path: Path) -> bool:
        """
        Checks if the internal storage has an usable copy of the game
        """
        return game_files_path.joinpath("super_metroid", "vanilla.smc").is_file()

    def delete_internal_copy(self, game_files_path: Path):
        """
        Deletes any copy of the game in the internal storage.
        """
        game_files_path.joinpath("super_metroid", "vanilla.smc").unlink(missing_ok=True)

    def default_output_file(self, seed_hash: str) -> str:
        """
        Provides a output file name with the given seed hash.
        :param seed_hash:
        :return:
        """
        return "SM Randomizer - {}".format(seed_hash)

    @property
    def valid_input_file_types(self) -> List[str]:
        return ["smc", "sfc"]

    @property
    def valid_output_file_types(self) -> List[str]:
        return ["smc", "sfc"]

    def create_patch_data(self, description: LayoutDescription, players_config: PlayersConfiguration,
                          cosmetic_patches: SuperMetroidCosmeticPatches) -> dict:
        """
        Creates a JSON serializable dict that can be used to patch the game.
        Intended to be ran on the server for multiworld.
        :return:
        """
        patches = description.all_patches[players_config.player_index]
        db = default_database.game_description_for(RandovaniaGame.SUPER_METROID)
        preset = description.permalink.get_preset(players_config.player_index)
        configuration = typing.cast(SuperMetroidConfiguration, preset.configuration)
        rng = Random(description.permalink.seed_number)

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
            "item_list": [
                sm_pickup_details_to_patcher(detail)
                for detail in pickup_list
            ],
            "starting_items": {
                item.long_name: quantity * _multiplier_for_item.get(item.long_name, 1)
                for item, quantity in patches.starting_items.items()
            },
        }

    def patch_game(self, input_file: Optional[Path], output_file: Path, patch_data: dict,
                   internal_copies_path: Path, progress_update: ProgressUpdateCallable):
        """
        Invokes the necessary tools to patch the game.
        :param input_file: Vanilla copy of the game. Required if uses_input_file_directly or has_internal_copy is False.
        :param output_file: Where a modified copy of the game is placed.
        :param patch_data: Data created by create_patch_data.
        :param internal_copies_path: Path to where all internal copies are stored.
        :param progress_update: Pushes updates as slow operations are done.
        :return: None
        """
        internal_copy = internal_copies_path.joinpath("super_metroid", "vanilla.smc")
        temporary_output = internal_copies_path.joinpath("super_metroid", "modified.smc")

        if input_file is not None:
            vanilla_bytes = input_file.read_bytes()
            if len(vanilla_bytes) == 0x300200:
                vanilla_bytes = vanilla_bytes[0x200:]

            if len(vanilla_bytes) != 0x300000:
                raise ValueError("Invalid input ROM")

            internal_copy.parent.mkdir(parents=True, exist_ok=True)
            internal_copy.write_bytes(vanilla_bytes)
        else:
            if not internal_copy.is_file():
                raise ValueError("Missing input ROM")
            vanilla_bytes = internal_copy.read_bytes()

        temporary_output.write_bytes(vanilla_bytes)

        item_list = [
            _json_to_pickup_placement_data(pickup)
            for pickup in patch_data["item_list"]
        ]
        starting_items = [
            SuperDuperMetroid.ROM_Patcher.PickupPlacementData(
                quantity_given=quantity,
                pickup_index=-1,
                item_name=name,
            )
            for name, quantity in patch_data["starting_items"]
        ]

        patches_to_apply = ["InstantG4", "MaxAmmoDisplay"]
        SuperDuperMetroid.ROM_Patcher.patch_rom(
            os.fspath(temporary_output),
            item_list=item_list,
            starting_items=starting_items,
            skip_intro=True,
            static_patches=patches_to_apply,
        )

        shutil.copy2(temporary_output, output_file)
