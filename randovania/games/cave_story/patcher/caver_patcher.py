import json
from pathlib import Path
from random import Random
import shutil
from typing import Optional
import typing
from randovania.games.game import RandovaniaGame
from randovania.game_description import default_database
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration
from randovania.games.cave_story.layout.cs_cosmetic_patches import CSCosmeticPatches
from randovania.games.cave_story.layout.preset_describer import get_ingame_hash
from randovania.games.cave_story.patcher.caver_music_shuffle import CaverMusic
from randovania.layout.layout_description import LayoutDescription
from randovania.lib.status_update_lib import ProgressUpdateCallable
from randovania.patching.patcher import Patcher
from randovania.interface_common.players_configuration import PlayersConfiguration


CSVERSION = 3

class CaverPatcher(Patcher):
    _busy: bool = False

    @property
    def is_busy(self) -> bool:
        return self._busy
    
    @property
    def export_can_be_aborted(self) -> bool:
        return False
    
    @property
    def uses_input_file_directly(self) -> bool:
        return False
    
    def has_internal_copy(self, game_files_path: Path) -> bool:
        return False
    
    def delete_internal_copy(self, game_files_path: Path):
        pass
    
    def default_output_file(self, seed_hash: str) -> str:
        return f"Cave Story Randomizer - {seed_hash}"
    
    @property
    def requires_input_file(self) -> bool:
        return False

    @property
    def valid_input_file_types(self) -> list[str]:
        return None
    
    @property
    def valid_output_file_types(self) -> list[str]:
        return [""]
    
    def create_patch_data(self, description: LayoutDescription, players_config: PlayersConfiguration, cosmetic_patches: CSCosmeticPatches) -> dict:
        preset = description.get_preset(players_config.player_index)
        configuration = typing.cast(CSConfiguration, preset.configuration)
        patches = description.all_patches[players_config.player_index]
        game_description = default_database.game_description_for(RandovaniaGame.CAVE_STORY)
        item_database = default_database.item_database_for_game(RandovaniaGame.CAVE_STORY)
        
        music_rng = Random(description.permalink.seed_number)
        mychar_rng = Random(description.permalink.seed_number)

        pickups = {area.extra["map_name"]: {} for area in game_description.world_list.all_areas}
        for index, target in patches.pickup_assignment.items():
            if target.player != players_config.player_index:
                raise NotImplementedError("Multiworld is not supported for Cave Story")
            
            node = game_description.world_list.node_from_pickup_index(index)
            area = game_description.world_list.nodes_to_area(node)

            mapname = node.extra.get("event_map", area.extra["map_name"])
            event = node.extra["event"]
            pickups[mapname][event] = item_database.get_item_with_name(target.pickup.name).extra.get("script", "<EVE0000") # TODO: proper nothing item script

        music = CaverMusic.get_shuffled_mapping(music_rng, cosmetic_patches)

        entrances = {} # TODO: entrance rando

        mapnames = pickups.keys() | music.keys() | entrances.keys()
        maps = {mapname: {
            "pickups": pickups.get(mapname, {}),
            "music": music.get(mapname, {}),
            "entrances": entrances.get(mapname, {})
        } for mapname in mapnames}

        return {
            "maps": maps,
            "mychar": cosmetic_patches.mychar.mychar_bmp(mychar_rng),
            "hash": get_ingame_hash(description._shareable_hash_bytes)
        }

    
    def patch_game(self, input_file: Optional[Path], output_file: Path, patch_data: dict, internal_copies_path: Path, progress_update: ProgressUpdateCallable):
        with output_file.joinpath("patcher.json").open("w") as f:
            json.dump(patch_data, f, indent=4)
