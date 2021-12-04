import json
from pathlib import Path
from random import Random
from typing import Optional
import typing
from randovania.game_description.resources.resource_type import ResourceType
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

from caver import patcher as caver_patcher


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
        return f"Cave Story Randomizer"
    
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
        if players_config.is_multiworld:
            raise NotImplementedError("Multiworld is not supported for Cave Story")

        configuration: CSConfiguration = description.permalink.get_preset(players_config.player_index).configuration
        patches = description.all_patches[players_config.player_index]
        db = default_database.resource_database_for(RandovaniaGame.CAVE_STORY)
        game_description = default_database.game_description_for(RandovaniaGame.CAVE_STORY)
        item_database = default_database.item_database_for_game(RandovaniaGame.CAVE_STORY)
        
        music_rng = Random(description.permalink.seed_number)
        mychar_rng = Random(description.permalink.seed_number)

        pickups = {area.extra["map_name"]: {} for area in game_description.world_list.all_areas}
        for index, target in patches.pickup_assignment.items():
            if target.player != players_config.player_index:
                # TODO: will need to figure out what scripts to insert for other player's items
                pass
            
            node = game_description.world_list.node_from_pickup_index(index)
            area = game_description.world_list.nodes_to_area(node)

            mapname = node.extra.get("event_map", area.extra["map_name"])
            event = node.extra["event"]
            pickups[mapname][event] = item_database.get_item_with_name(target.pickup.name).extra.get("script", "<EVE0000") # TODO: proper nothing item script

        music = CaverMusic.get_shuffled_mapping(music_rng, cosmetic_patches)

        entrances = {} # TODO: entrance rando

        hints = {} # TODO

        mapnames = pickups.keys() | music.keys() | entrances.keys()
        maps = {mapname: {
            "pickups": pickups.get(mapname, {}),
            "music": music.get(mapname, {}),
            "entrances": entrances.get(mapname, {}),
            "hints": hints.get(mapname, {}),
        } for mapname in mapnames}

        # objective flags
        starting_script = configuration.objective.script
        # B2 falling blocks disable flag
        if configuration.no_blocks:
            starting_script += "<FL+1351"
        # rocket skip enabled
        if configuration.trick_level.level_for_trick(db.get_by_type_and_index(ResourceType.TRICK, "Dboost")).as_num >= 4:
            starting_script += "<FL+6400"
        # initialize HP counter to 3HP
        starting_script += "<FL+4011<FL+4012"
        # Camp and Labyrinth B CMP mapflags
        starting_script += "<MP+0040<MP+0043"
        # Softlock prevention mapflags
        starting_script += "<MP+0032<MP+0033<MP+0036"

        # TODO: allow any starting location

        # starting location flag and EVE/TRA
        if game_description.starting_location.area_name == "Start Point":
            starting_script += "<FL+6200<EVE0091"
        else:
            # flags set during first cave in normal gameplay
            starting_script += "<FL+0301<FL+0302<FL+1641<FL+1642<FL+0320<FL+0321"
            if game_description.starting_location.area_name == "Arthur's House":
                starting_script += "<FL+6201<TRA0001:0094:0008:0004"
            elif game_description.starting_location.area_name == "Camp":
                starting_script += "<FL+6202<TRA0040:0094:0014:0009"
        
        maps["Start"]["pickups"]["0201"] = starting_script

        return {
            "maps": maps,
            "mychar": cosmetic_patches.mychar.mychar_bmp(mychar_rng),
            "hash": get_ingame_hash(description._shareable_hash_bytes)
        }

    
    def patch_game(self, input_file: Optional[Path], output_file: Path, patch_data: dict, internal_copies_path: Path, progress_update: ProgressUpdateCallable):
        self._busy = True
        caver_patcher.patch_files(patch_data, output_file, progress_update)
        self._busy = False
