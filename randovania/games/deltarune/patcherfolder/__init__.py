import dataclasses
import typing
import json
from io import BytesIO
from pathlib import Path
from random import Random
from typing import List, Optional

from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.game import RandovaniaGame
from randovania.games.deltarune.layout.deltarune_configuration import deltaruneConfiguration
from randovania.games.deltarune.layout.deltarune_cosmetic_patches import deltaruneCosmeticPatches
from randovania.generator.item_pool import pickup_creator
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib.status_update_lib import ProgressUpdateCallable
from randovania.patching.patcher import Patcher
from randovania.patching.prime.patcher_file_lib import pickup_exporter

def deltarune_pickup_details_to_patcher(detail: pickup_exporter.ExportedPickupDetails
                                 ) -> dict:
    if detail.model.game == RandovaniaGame.DELTARUNE:
        model_name = detail.model.name
    else:
        model_name = "Nothing"

    scan_text = detail.scan_text
    hud_text = detail.hud_text[0]
    pickup_type = -1
    count = 0
    prog = 0
    
    if len(detail.conditional_resources) > 1:
        prog = 1
    for resource, quantity in detail.conditional_resources[0].resources:
        if resource.resource_type == ResourceType.ITEM and resource.extra["item_id"] >= 1000:
            continue
        pickup_type = resource.extra["item_id"]
        count = quantity
        break
        


    result = {
        "item_index": pickup_type,
        "quantity_given": count,
        "pickup_index": detail.index.index,
        "owner_name": None,
        "progressive": prog
    }

    return result

def deltarune_starting_items_to_patcher(item: ItemResourceInfo, quantity: int, detail: pickup_exporter.ExportedPickupDetails) -> dict:
    result = {
        "item_index": item.extra["item_id"],
        "quantity_given": quantity
    }
    print(str(item.extra["item_id"]))
    return result

def copyDir(folder: Path, to: Path):
    for d in folder.iterdir():
        if (d.is_file()):
            Path(to.joinpath(d.name)).touch(exist_ok=True)
            fl = Path(to.joinpath(d.name))
            fl.write_bytes(d.read_bytes())
        elif (d.is_dir()):
            Path(to.joinpath(d.name)).mkdir(exist_ok=True)
            copyDir(Path(folder.joinpath(d.name)),to.joinpath(d.name))

class PatcherMaker(Patcher):

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
        return False

    def delete_internal_copy(self, game_files_path: Path):
        """
        Deletes any copy of the game in the internal storage.
        """
        pass

    def default_output_file(self, seed_hash: str) -> str:
        """
        Provides a output file name with the given seed hash.
        :param seed_hash:
        :return:
        """
        return f"Deltarune Randomizer"
        
    @property
    def requires_input_file(self) -> bool:
        return True

    @property
    def valid_input_file_types(self) -> List[str]:
        return [""]

    @property
    def valid_output_file_types(self) -> List[str]:
        return [""]

    def create_patch_data(self, description: LayoutDescription, players_config: PlayersConfiguration,
                          cosmetic_patches: deltaruneCosmeticPatches) -> dict:
        """
        Creates a JSON serializable dict that can be used to patch the game.
        Intended to be ran on the server for multiworld.
        :return:
        """
        patches = description.all_patches[players_config.player_index]
        db = default_database.game_description_for(RandovaniaGame.DELTARUNE)
        preset = description.get_preset(players_config.player_index)
        configuration = typing.cast(deltaruneConfiguration, preset.configuration)
        rng = Random(description.get_seed_for_player(players_config.player_index))
        
        if players_config.is_multiworld:
            raise NotImplementedError("Multiworld is not supported for DELTARUNE")
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

        starting_point = patches.starting_location

        starting_area = db.world_list.area_by_area_location(starting_point)

        starting_location_info = {
            "starting_region": starting_point.world_name,
        }
        return {
            "pickups": [
                deltarune_pickup_details_to_patcher(detail)
                for detail in pickup_list
            ],
            "starting_items": [
                deltarune_starting_items_to_patcher(item, qty, detail)
                for detail in pickup_list
                for item, qty in patches.starting_items.items()
            ],
            "starting_conditions": starting_location_info
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
        
        self._busy = True
        import subprocess
        print(str(input_file.joinpath("*")))
        Path(output_file.joinpath("Deltarune Randomizer")).mkdir(exist_ok=True)
        tomakepath = Path(output_file.joinpath("Deltarune Randomizer"))
        copyDir(input_file,tomakepath)
        subprocess.run([str(Path(__file__).parent.joinpath("..","deltapatcher","xdelta.exe")), '-f', '-d','-s',str(input_file.joinpath("data.win")), str(Path(__file__).parent.joinpath("..","deltapatcher","PATCH THIS.xdelta")),str(tomakepath.joinpath("data.win"))],check=True)
        Path(tomakepath).joinpath("Deltarune Randomizer Seed.txt").unlink(missing_ok=True)
        with Path(tomakepath).joinpath("Deltarune Randomizer Seed.txt").open("w") as f:
            for item in patch_data["pickups"]:
                f.write(str(item["pickup_index"]))
                f.write('\n')
                f.write(str(item["item_index"]))
                f.write('\n')
                f.write(str(item["progressive"]))
                f.write('\n')
            for item in patch_data["starting_items"]:
                f.write(str(item["item_index"]))
                f.write('\n')
        self._busy = False