import json
from pathlib import Path
from random import Random
from typing import Optional
import typing
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.hint import HintLocationPrecision
from randovania.game_description.item.item_category import USELESS_ITEM_CATEGORY
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.resources.resource_info import ResourceGainTuple
from randovania.game_description.world import world_list
from randovania.game_description.world.node import LogbookNode
from randovania.patching.prime.patcher_file_lib.hint_formatters import LocationFormatter
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.world_list import WorldList
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
from randovania.patching.prime.patcher_file_lib import hint_lib
from randovania.patching.prime.patcher_file_lib.hint_formatters import RelativeAreaFormatter, TemplatedFormatter

from randovania.patching.prime.patcher_file_lib.hints import create_location_formatters, get_hints_for_asset
from randovania.patching.prime.patcher_file_lib.item_hints import RelativeItemFormatter

from tsc_utils.numbers import num_to_tsc_value, tsc_value_to_num
from tsc_utils.flags import set_flag


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
        hint_rng = Random(description.permalink.seed_number)

        nothing_item = PickupTarget(PickupEntry(
            "Nothing",
            PickupModel(RandovaniaGame.CAVE_STORY, "Nothing"),
            USELESS_ITEM_CATEGORY,
            USELESS_ITEM_CATEGORY,
            tuple()
        ), players_config.player_index)
        nothing_item_script = "<PRI<MSG<TUR<IT+0000\r\nGot =Nothing=!<WAI0025<NOD<EVE0015"

        pickups = {area.extra["map_name"]: {} for area in game_description.world_list.all_areas}
        for index in sorted(game_description.world_list._pickup_index_to_node.keys()):
            target = patches.pickup_assignment.get(index, nothing_item)

            if target.player != players_config.player_index:
                # TODO: will need to figure out what scripts to insert for other player's items
                pass
            
            node = game_description.world_list.node_from_pickup_index(index)
            area = game_description.world_list.nodes_to_area(node)

            mapname = node.extra.get("event_map", area.extra["map_name"])
            event = node.extra["event"]
            
            if target == nothing_item:
                pickup_script = nothing_item_script
            else:
                pickup_script = item_database.get_item_with_name(target.pickup.name).extra.get("script", nothing_item_script)
            pickups[mapname][event] = pickup_script

        music = CaverMusic.get_shuffled_mapping(music_rng, cosmetic_patches)

        entrances = {} # TODO: entrance rando

        hints_for_asset = get_hints(description.all_patches, players_config, hint_rng)
        hints = {}
        for logbook_node in game_description.world_list.all_nodes:
            if not isinstance(logbook_node, LogbookNode):
                continue
                
            mapname = logbook_node.extra.get("event_map", game_description.world_list.nodes_to_area(logbook_node).extra["map_name"])
            event = logbook_node.extra["event"]
            
            if hints.get(mapname) is None:
                hints[mapname] = {}
            hints[mapname][event] = {
                "text": hints_for_asset[logbook_node.string_asset_id],
                "facepic": logbook_node.extra.get("facepic", "0000"),
                "ending": logbook_node.extra.get("ending", "<END")
            }

        mapnames = pickups.keys() | music.keys() | entrances.keys()
        maps = {mapname: {
            "pickups": pickups.get(mapname, {}),
            "music": music.get(mapname, {}),
            "entrances": entrances.get(mapname, {}),
            "hints": hints.get(mapname, {}),
        } for mapname in sorted(mapnames)}

        # objective flags
        starting_script = configuration.objective.script
        # B2 falling blocks disable flag
        if configuration.no_blocks:
            starting_script += "<FL+1351"
        # rocket skip enabled
        if configuration.trick_level.level_for_trick(db.get_by_type_and_index(ResourceType.TRICK, "Dboost")).as_number >= 4:
            starting_script += "<FL+6400"
        # initialize HP counter
        starting_script += set_flag(4011, configuration.starting_hp, bits=6)
        # Camp and Labyrinth B CMP mapflags
        starting_script += "<MP+0040<MP+0043"
        # Softlock prevention mapflags
        starting_script += "<MP+0032<MP+0033<MP+0036"

        # Starting HP
        if configuration.starting_hp != 3:
            starting_script += f"<ML+{num_to_tsc_value(configuration.starting_hp - 3).decode('utf-8')}"

        # Starting Items
        if len(patches.starting_items):
            starting_script += "\r\n<PRI<MSG<TUR"
        
        equip_num = 0
        items_extra = ""
        trades = {
            "blade": 0,
            "fireball": 0,
            "keys": 0,
            "medals": 0,
            "lewd": 0,
            "sprinklers": 0,
            "mushrooms": 0,
            "none": 0,
        }
        life = 0

        missile = next((res for res in patches.starting_items.keys() if res.short_name in {"missile", "tempMissile"}), None)
        for item in patches.starting_items.keys():
            if item.resource_type != ResourceType.ITEM or item == missile:
                continue

            if item.short_name == "lifeCapsule":
                life = patches.starting_items[item]
                continue

            if item.short_name == "puppies":
                num_puppies = patches.starting_items[item]

                flags = "".join([f"<FL+{num_to_tsc_value(5001+i).decode('utf-8')}" for i in range(num_puppies)])
                flags += "<FL+0274"
                if num_puppies == 5:
                    flags += "<FL+0593"
                
                words = {
                    1: "a",
                    2: "a second",
                    3: "a third",
                    4: "a fourth",
                    5: "the last"
                }

                starting_script += (
                    f"<IT+0014<GIT1014{flags}<SNP0136:0000:0000:0000\r\n"
                    f"Got {words[num_puppies]} =Puppy=!<WAI0010<NOD\r\n<CLR"
                )
                continue

            if item.extra.get("text") is None:
                raise ValueError(f"{item.long_name} is not a valid starting item!")

            item_num = item.extra.get("it+")
            arms_num = item.extra.get("am+")
            if (item_num is None) == (arms_num is None):
                raise ValueError(f"{item.long_name} must define exactly one of item_num and arms_num.")

            equip_num |= item.extra.get("equip", 0)
            items_extra += item.extra.get("extra", "")
            trade = item.extra.get("trade", "none")
            trades[trade] += 1

            git = num_to_tsc_value(arms_num or item_num + 1000).decode('utf-8')
            ammo = num_to_tsc_value(item.extra.get("ammo", 0)).decode('utf-8')
            if item.short_name in {"missiles", "supers"}:
                ammo = num_to_tsc_value(patches.starting_items[missile]).decode('utf-8')
            plus = f"<IT+{num_to_tsc_value(item_num).decode('utf-8')}" if item_num else f"<AM+{num_to_tsc_value(arms_num).decode('utf-8')}:{ammo}"
            flag = num_to_tsc_value(item.extra["flag"]).decode('utf-8')
            text = item.extra["text"]

            starting_script += f"<GIT{git}{plus}<FL+{flag}\r\n{text}<WAI0010<NOD\r\n<CLR"

            if trades[trade] >= 2:
                # we do this mid-loop, even though it duplicates them for the keys.
                # otherwise, starting with *everything* can cause some items to be
                # missed due to inventory overflow
                if trade == "keys":
                    starting_script += "<IT-0001<IT-0003<IT-0009<IT-0010<IT-0017<IT-0025"
                if trade == "medals":
                    starting_script += "<IT-0031<IT-0036"
                if trade == "lewd":
                    starting_script += "<IT-0035<IT-0037"
                if trade == "sprinklers":
                    starting_script += "<IT-0028<IT-0029"
                if trade == "mushrooms":
                    starting_script += "<IT-0033<IT-0034"

        if len(patches.starting_items):
            starting_script += items_extra
            starting_script += f"<EQ+{num_to_tsc_value(equip_num).decode('utf-8')}\r\n"
            
            if life > 0:
                starting_script += (
                    f"<GIT1006Got a =Life Capsule=!<ML+{num_to_tsc_value(life).decode('utf-8')}\r\n"
                    f"Max health increased by\r\n"
                    f"{life}!<WAI0010<NOD\r\n<CLR"
                )

            starting_script += "<GIT0000\r\n"

            if trades["blade"] >= 2:
                starting_script += (
                    "You may trade the =Nemesis=\r\n"
                    "with the =Blade= and vice-versa\r\n"
                    "at the computer in Arthur's House.<WAI0025<NOD<FL+2811\r\n<CLR"
                )
            
            if trades["fireball"] >= 2:
                starting_script += (
                    "You may trade the =Fireball=\r\n"
                    "with the =Snake= and vice-versa\r\n"
                    "at the computer in Arthur's House.<WAI0025<NOD<FL+2802\r\n<CLR"
                )
            
            # Consolidation items
            if trades["keys"] >= 2:
                starting_script += "<IT+0040"
            if trades["medals"] >= 2:
                starting_script += "<IT+0041"
            if trades["lewd"] >= 2:
                starting_script += "<IT+0042"
            if trades["sprinklers"] >= 2:
                starting_script += "<IT+0043"
            if trades["mushrooms"] >= 2:
                starting_script += "<IT+0044"

            starting_script += "<CLO"

        # Starting Locations
        if patches.starting_location.area_name in {"Start Point", "First Cave", "Hermit Gunsmith"}:
            # started in first cave
            starting_script += "<FL+6200"
        else:
            # flags set during first cave in normal gameplay
            starting_script += "<FL+0301<FL+0302<FL+1641<FL+1642<FL+0320<FL+0321"
            waterway = {"Waterway", "Waterway Cabin", "Main Artery"}
            if patches.starting_location.world_name == "Labyrinth" and patches.starting_location.area_name not in waterway:
                # started near camp; disable camp collision
                starting_script += "<FL+6202"
            elif (patches.starting_location.world_name != "Mimiga Village" and patches.starting_location.area_name not in waterway) or patches.starting_location.area_name == "Arthur's House":
                # started outside mimiga village
                starting_script += "<FL+6201"
        
        starting_script += game_description.world_list.area_by_area_location(patches.starting_location).extra["starting_script"]
        
        maps["Start"]["pickups"]["0201"] = starting_script

        return {
            "maps": maps,
            "other_tsc": {},
            "mychar": cosmetic_patches.mychar.mychar_bmp(mychar_rng),
            "hash": get_ingame_hash(description._shareable_hash_bytes)
        }
    
    def patch_game(self, input_file: Optional[Path], output_file: Path, patch_data: dict, internal_copies_path: Path, progress_update: ProgressUpdateCallable):
        self._busy = True
        try:
            caver_patcher.patch_files(patch_data, output_file, progress_update)
        finally:
            self._busy = False

def create_loc_formatters(area_namer: hint_lib.AreaNamer, world_list: WorldList, patches: GamePatches, players_config: PlayersConfiguration) -> dict[HintLocationPrecision, LocationFormatter]:
    return {
        HintLocationPrecision.MALCO: TemplatedFormatter(
            "BUT ALL I KNOW HOW TO DO IS MAKE {determiner.upper}{pickup}...", area_namer, upper_pickup=True, text_color=None
        ),
        HintLocationPrecision.JENKA: TemplatedFormatter(
            "perhaps I'll give you {determiner}{pickup} in return...", area_namer, text_color=None
        ),
        HintLocationPrecision.LITTLE: TemplatedFormatter(
            "He was exploring the island with {determiner}{pickup}...", area_namer, text_color=None
        ),
        HintLocationPrecision.NUMAHACHI: TemplatedFormatter(
            "{determiner.capitalize}{pickup}.", area_namer, text_color=None
        ),
        HintLocationPrecision.DETAILED: TemplatedFormatter("{{start}} {determiner}{pickup} {{mid}} in {node}.",
                                                           area_namer, text_color=None),
        HintLocationPrecision.WORLD_ONLY: TemplatedFormatter("{{start}} {determiner}{pickup} {{mid}} in {node}.",
                                                             area_namer, text_color=None),
        HintLocationPrecision.RELATIVE_TO_AREA: RelativeAreaFormatter(world_list, patches, None),
        HintLocationPrecision.RELATIVE_TO_INDEX: RelativeItemFormatter(world_list, patches, players_config, None),
    }

def get_hints(all_patches: dict[int, GamePatches], players_config: PlayersConfiguration, hint_rng: Random):
    game_description = default_database.game_description_for(RandovaniaGame.CAVE_STORY)
    area_namers = {index: hint_lib.AreaNamer(game_description.world_list, include_world=False)
                   for index in players_config.player_names.keys()}
        
        
    hints_for_asset = get_hints_for_asset(all_patches, players_config, game_description.world_list, area_namers, hint_rng, create_loc_formatters, RandovaniaGame.CAVE_STORY, None, None)
    
    starts = ["I hear that", "Rumour has it,", "They say"]
    mids = ["can be found", "is", "is hidden"]
    return {
        asset_id: hint.format(start=hint_rng.choice(starts), mid=hint_rng.choice(mids))
        for asset_id, hint in hints_for_asset.items()
    }
