from random import Random

from tsc_utils.flags import set_flag
from tsc_utils.numbers import num_to_tsc_value

from randovania.exporter.hints.hint_exporter import HintExporter
from randovania.exporter.hints.joke_hints import JOKE_HINTS
from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.item.item_category import USELESS_ITEM_CATEGORY
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.node import LogbookNode, PickupNode
from randovania.games.cave_story.exporter.hint_namer import CSHintNamer
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration
from randovania.games.cave_story.layout.cs_cosmetic_patches import CSCosmeticPatches
from randovania.games.cave_story.layout.preset_describer import get_ingame_hash
from randovania.games.cave_story.patcher.caver_music_shuffle import CaverMusic
from randovania.games.game import RandovaniaGame
from randovania.interface_common.players_configuration import PlayersConfiguration


class CSPatchDataFactory(BasePatchDataFactory):
    cosmetic_patches: CSCosmeticPatches
    configuration: CSConfiguration

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.CAVE_STORY

    def create_data(self) -> dict:
        if self.players_config.is_multiworld:
            raise NotImplementedError("Multiworld is not supported for Cave Story")

        game_description = self.game
        seed_number = self.description.get_seed_for_player(self.players_config.player_index)
        music_rng = Random(seed_number)
        mychar_rng = Random(seed_number)
        hint_rng = Random(seed_number)

        nothing_item = PickupTarget(PickupEntry(
            "Nothing",
            PickupModel(RandovaniaGame.CAVE_STORY, "Nothing"),
            USELESS_ITEM_CATEGORY,
            USELESS_ITEM_CATEGORY,
            tuple()
        ), self.players_config.player_index)
        nothing_item_script = "<PRI<MSG<TUR<IT+0000\r\nGot =Nothing=!<WAI0025<NOD<EVE0015"

        pickups = {area.extra["map_name"]: {} for area in game_description.world_list.all_areas}
        for index in sorted(node.pickup_index for node in game_description.world_list.all_nodes
                            if isinstance(node, PickupNode)):
            target = self.patches.pickup_assignment.get(index, nothing_item)

            if target.player != self.players_config.player_index:
                # TODO: will need to figure out what scripts to insert for other player's items
                pass

            node = game_description.world_list.node_from_pickup_index(index)
            area = game_description.world_list.nodes_to_area(node)

            mapname = node.extra.get("event_map", area.extra["map_name"])
            event = node.extra["event"]

            if target == nothing_item:
                pickup_script = nothing_item_script
            else:
                pickup_script = self.item_db.get_item_with_name(target.pickup.name).extra.get("script",
                                                                                              nothing_item_script)
            pickups[mapname][event] = pickup_script

        music = CaverMusic.get_shuffled_mapping(music_rng, self.cosmetic_patches)

        entrances = {}  # TODO: entrance rando

        hints_for_asset = get_hints(self.description.all_patches, self.players_config, hint_rng)
        hints = {}
        for logbook_node in game_description.world_list.all_nodes:
            if not isinstance(logbook_node, LogbookNode):
                continue

            mapname = logbook_node.extra.get("event_map",
                                             game_description.world_list.nodes_to_area(logbook_node).extra["map_name"])
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
        starting_script = self.configuration.objective.script
        # B2 falling blocks disable flag
        if self.configuration.no_blocks:
            starting_script += "<FL+1351"
        # rocket skip enabled
        if self.configuration.trick_level.level_for_trick(
                self.game.resource_database.get_by_type_and_index(ResourceType.TRICK, "Dboost")).as_number >= 4:
            starting_script += "<FL+6400"
        # initialize HP counter
        starting_script += set_flag(4011, self.configuration.starting_hp, bits=6)
        # Camp and Labyrinth B CMP mapflags
        starting_script += "<MP+0040<MP+0043"
        # Softlock prevention mapflags
        starting_script += "<MP+0032<MP+0033<MP+0036"

        # Starting Items
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

        starting_msg = ""
        missile = next((res for res in self.patches.starting_items.keys()
                        if res.short_name in {"missile", "tempMissile"}),
                       None)
        for item in self.patches.starting_items.keys():
            if item.resource_type != ResourceType.ITEM or item == missile:
                continue

            if item.short_name == "lifeCapsule":
                life = self.patches.starting_items[item]
                continue

            if item.short_name == "puppies":
                num_puppies = self.patches.starting_items[item]

                flags = "".join([f"<FL+{num_to_tsc_value(5001 + i).decode('utf-8')}" for i in range(num_puppies)])
                flags += "<FL+0274"
                if num_puppies == 5:
                    flags += "<FL+0593"

                words = {
                    1: "a =Puppy=",
                    2: "two =Puppies=",
                    3: "three =Puppies=",
                    4: "four =Puppies=",
                    5: "all five =Puppies="
                }

                starting_msg += (
                    f"<IT+0014<GIT1014{flags}<SNP0136:0000:0000:0000\r\n"
                    f"Got {words[num_puppies]}!<WAI0010<NOD\r\n<CLR"
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
                ammo = num_to_tsc_value(self.patches.starting_items[missile]).decode('utf-8')
            plus = f"<IT+{num_to_tsc_value(item_num).decode('utf-8')}" if item_num else f"<AM+{num_to_tsc_value(arms_num).decode('utf-8')}:{ammo}"
            flag = num_to_tsc_value(item.extra["flag"]).decode('utf-8')
            text = item.extra["text"]

            starting_msg += f"<GIT{git}{plus}<FL+{flag}\r\n{text}<WAI0010<NOD\r\n<CLR"

            if trades[trade] >= 2:
                # we do this mid-loop, even though it duplicates them for the keys.
                # otherwise, starting with *everything* can cause some items to be
                # missed due to inventory overflow
                if trade == "keys":
                    starting_msg += "<IT-0001<IT-0003<IT-0009<IT-0010<IT-0017<IT-0025"
                if trade == "medals":
                    starting_msg += "<IT-0031<IT-0036"
                if trade == "lewd":
                    starting_msg += "<IT-0035<IT-0037"
                if trade == "sprinklers":
                    starting_msg += "<IT-0028<IT-0029"
                if trade == "mushrooms":
                    starting_msg += "<IT-0033<IT-0034"

        if len(self.patches.starting_items):
            starting_msg += items_extra

            if life > 0:
                starting_msg += (
                    f"<GIT1006Got a =Life Capsule=!<ML+{num_to_tsc_value(life).decode('utf-8')}\r\n"
                    f"Max health increased by\r\n"
                    f"{life}!<WAI0010<NOD\r\n<CLR"
                )

            if starting_msg:
                starting_msg += "<GIT0000\r\n"

            if trades["blade"] >= 2:
                starting_msg += (
                    "You may trade the =Nemesis=\r\n"
                    "with the =Blade= and vice-versa\r\n"
                    "at the computer in Arthur's House.<WAI0025<NOD<FL+2811\r\n<CLR"
                )

            if trades["fireball"] >= 2:
                starting_msg += (
                    "You may trade the =Fireball=\r\n"
                    "with the =Snake= and vice-versa\r\n"
                    "at the computer in Arthur's House.<WAI0025<NOD<FL+2802\r\n<CLR"
                )

            # Consolidation items
            if trades["keys"] >= 2:
                starting_msg += "<IT+0040"
            if trades["medals"] >= 2:
                starting_msg += "<IT+0041"
            if trades["lewd"] >= 2:
                starting_msg += "<IT+0042"
            if trades["sprinklers"] >= 2:
                starting_msg += "<IT+0043"
            if trades["mushrooms"] >= 2:
                starting_msg += "<IT+0044"

        if starting_msg:
            starting_script += f"\r\n<PRI<MSG<TUR{starting_msg}<CLO"

        starting_script += f"<EQ+{num_to_tsc_value(equip_num).decode('utf-8')}\r\n"

        # Starting HP
        if self.configuration.starting_hp != 3 or life > 0:
            starting_script += f"<ML+{num_to_tsc_value(self.configuration.starting_hp + life - 3).decode('utf-8')}"

        # Starting Locations
        if self.patches.starting_location.area_name in {"Start Point", "First Cave", "Hermit Gunsmith"}:
            # started in first cave
            starting_script += "<FL+6200"
        else:
            # flags set during first cave in normal gameplay
            starting_script += "<FL+0301<FL+0302<FL+1641<FL+1642<FL+0320<FL+0321"
            waterway = {"Waterway", "Waterway Cabin", "Main Artery"}
            world_name, area_name = self.patches.starting_location.as_tuple
            if world_name == "Labyrinth" and area_name not in waterway:
                # started near camp; disable camp collision
                starting_script += "<FL+6202"
            elif (world_name != "Mimiga Village" and area_name not in waterway) or area_name == "Arthur's House":
                # started outside mimiga village
                starting_script += "<FL+6201"

        tra = game_description.world_list.area_by_area_location(self.patches.starting_location).extra["starting_script"]
        starting_script += tra

        # Softlock debug cat warps
        softlock_warps = {
            mapname: area.extra["softlock_warp"]
            for area in game_description.world_list.all_areas
            if area.extra.get("softlock_warp") is not None
            for mapname in area.extra.get("softlock_maps", [area.extra["map_name"]])
        }
        for mapname, event in softlock_warps.items():
            maps[mapname]["pickups"][event] = tra

        maps["Start"]["pickups"]["0201"] = starting_script

        # Configurable missile ammo
        small_missile_ammo = self.item_db.ammo["Missile Expansion"]
        hell_missile_ammo = self.item_db.ammo["Large Missile Expansion"]

        ammo_state = self.configuration.ammo_configuration.items_state
        small_missile = ammo_state[small_missile_ammo].ammo_count[0]
        hell_missile = ammo_state[hell_missile_ammo].ammo_count[0]
        base_missiles = self.patches.starting_items[missile]
        missile_id = "0005"
        supers_id = "0010"
        missile_events = {
            "0030": (missile_id, small_missile + base_missiles),  # normal launcher
            "0031": (missile_id, small_missile),  # normal expansion
            "0032": (supers_id, small_missile),  # supers expansion
            "0035": (missile_id, hell_missile + base_missiles),  # normal hell launcher
            "0036": (missile_id, hell_missile),  # normal hell expansion
            "0037": (supers_id, hell_missile),  # supers hell expansion
            "0038": (supers_id, base_missiles)  # supers launcher
        }
        head = {}
        for event, m_ammo in missile_events.items():
            head[event] = {
                "needle": f"<AM%+....:....",
                "script": f"<AM+{m_ammo[0]}:{num_to_tsc_value(m_ammo[1]).decode('utf-8')}"
            }

        life_capsules = [("Small Life Capsule", "0012"), ("Medium Life Capsule", "0013"),
                         ("Large Life Capsule", "0014")]
        for name, event in life_capsules:
            amount = \
            self.configuration.major_items_configuration.items_state[self.item_db.major_items[name]].included_ammo[
                0]
            head[event] = {
                "needle": f".!<ML%+....",
                "script": f"{amount}!<ML+{num_to_tsc_value(amount).decode('utf-8')}"
            }

        return {
            "maps": maps,
            "other_tsc": {
                "Head": head
            },
            "mychar": self.cosmetic_patches.mychar.mychar_bmp(mychar_rng),
            "hash": get_ingame_hash(self.description.shareable_hash_bytes)
        }


def get_hints(all_patches: dict[int, GamePatches], players_config: PlayersConfiguration, hint_rng: Random):
    namer = CSHintNamer(all_patches, players_config)
    exporter = HintExporter(namer, hint_rng, JOKE_HINTS)

    hints_for_asset: dict[LogbookAsset, str] = {}
    for asset, hint in all_patches[players_config.player_index].hints.items():
        hints_for_asset[asset] = exporter.create_message_for_hint(hint, all_patches, players_config, True)

    starts = ["I hear that", "Rumour has it,", "They say"]
    mids = ["can be found", "is", "is hidden"]
    return {
        asset.asset_id: hint.format(start=hint_rng.choice(starts), mid=hint_rng.choice(mids))
        for asset, hint in hints_for_asset.items()
    }
