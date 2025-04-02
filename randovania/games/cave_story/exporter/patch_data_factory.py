from __future__ import annotations

import typing
from collections import defaultdict
from random import Random
from typing import TYPE_CHECKING, override

from caver.patcher import wrap_msg_text
from tsc_utils.flags import set_flag
from tsc_utils.numbers import num_to_tsc_value

from randovania.exporter.hints.joke_hints import GENERIC_JOKE_HINTS
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.cave_story.exporter.hint_exporter import CSHintExporter
from randovania.games.cave_story.exporter.hint_namer import CSHintNamer
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration
from randovania.games.cave_story.layout.cs_cosmetic_patches import CSCosmeticPatches
from randovania.games.cave_story.layout.preset_describer import get_ingame_hash
from randovania.games.cave_story.patcher.caver_music_shuffle import CaverMusic
from randovania.generator.pickup_pool import pickup_creator

if TYPE_CHECKING:
    from caver.schema import (
        CaverData,
        CaverdataMaps,
        CaverdataMapsHints,
        CaverdataOtherTsc,
        EventNumber,
        MapName,
        TscScript,
    )

    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_info import ResourceInfo

NOTHING_ITEM_SCRIPT = "<PRI<MSG<TUR<IT+0000\r\nGot =Nothing=!<WAI0025<NOD<EVE0015"


class CSPatchDataFactory(PatchDataFactory[CSConfiguration, CSCosmeticPatches]):
    # Variables shared between multiple functions
    _seed_number: int
    _maps: dict[MapName, CaverdataMaps]
    _equip_num: int
    _items_extra: str
    _trades: dict[str, int]
    _life: int
    _starting_items: ResourceCollection
    _missile: ResourceInfo | None

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.CAVE_STORY

    @override
    @classmethod
    def hint_namer_type(cls) -> type[CSHintNamer]:
        return CSHintNamer

    @override
    @classmethod
    def hint_exporter_type(cls) -> type[CSHintExporter]:
        return CSHintExporter

    def create_game_specific_data(self) -> dict:
        self._seed_number = self.description.get_seed_for_world(self.players_config.player_index)

        self._maps = self._create_maps_data()
        self._maps["Start"]["pickups"]["0201"] = self._create_starting_script()

        data: CaverData = {
            "maps": self._maps,
            "other_tsc": {"Head": self._head_tsc_edits()},
            "mychar": self.cosmetic_patches.mychar.mychar_bmp(Random(self._seed_number)),
            "hash": get_ingame_hash(self.description.shareable_hash_bytes),
            "uuid": f"{{{self.players_config.get_own_uuid()}}}",
        }
        return typing.cast("dict", data)

    def _create_maps_data(self) -> dict[MapName, CaverdataMaps]:
        pickups = self._create_pickups_data()
        music = CaverMusic.get_shuffled_mapping(Random(self._seed_number), self.cosmetic_patches)
        entrances = self._create_entrance_data()
        hints = self._create_hints_data()

        mapnames = pickups.keys() | music.keys() | entrances.keys() | hints.keys()
        maps: dict[MapName, CaverdataMaps] = {
            mapname: {
                "pickups": pickups[mapname],
                "music": music[mapname],
                "entrances": entrances[mapname],
                "hints": hints[mapname],
            }
            for mapname in sorted(mapnames)
        }

        # Softlock debug cat warps
        softlock_warps = {
            mapname: area.extra["softlock_warp"]
            for area in self.game.region_list.all_areas
            if area.extra.get("softlock_warp") is not None
            for mapname in area.extra.get("softlock_maps", [area.extra["map_name"]])
        }
        for mapname, event in softlock_warps.items():
            maps[mapname]["pickups"][event] = self._tra_for_warp_to_start()

        return maps

    def _create_pickups_data(self) -> dict[MapName, dict[EventNumber, TscScript]]:
        nothing_item = PickupTarget(
            pickup_creator.create_visual_nothing(RandovaniaGame.CAVE_STORY, "Nothing", "Nothing"),
            self.players_config.player_index,
        )

        pickups: dict[MapName, dict[EventNumber, TscScript]] = defaultdict(dict)
        for index in sorted(node.pickup_index for node in self.game.region_list.iterate_nodes_of_type(PickupNode)):
            target = self.patches.pickup_assignment.get(index, nothing_item)

            node = self.game.region_list.node_from_pickup_index(index)
            area = self.game.region_list.nodes_to_area(node)

            mapname = typing.cast("MapName", node.extra.get("event_map", area.extra["map_name"]))
            event = typing.cast("EventNumber", node.extra["event"])

            if not self.players_config.should_target_local_player(target.player):
                message = f"Sent ={target.pickup.name}= to ={self.players_config.player_names[target.player]}=!"
                message = wrap_msg_text(message, False, ending="<WAI0025<NOD")
                git = "<GIT0000"  # TODO: add GIT info in pickup db and use it here (respecting offworld models)
                pickup_script = f"<PRI<MSG<TUR<IT+0000{git}{message}<EVE0015"
            elif target == nothing_item:
                pickup_script = NOTHING_ITEM_SCRIPT
            else:
                pickup_script = self.pickup_db.get_pickup_with_name(target.pickup.name).extra.get(
                    "script", NOTHING_ITEM_SCRIPT
                )
            pickups[mapname][event] = pickup_script

        return pickups

    def _create_entrance_data(self) -> dict[MapName, dict[EventNumber, TscScript]]:
        return defaultdict(dict)  # TODO: entrance rando

    def _create_hints_data(self) -> dict[MapName, dict[EventNumber, CaverdataMapsHints]]:
        hint_rng = Random(self._seed_number)

        exporter = self.get_hint_exporter(
            self.description.all_patches,
            self.players_config,
            hint_rng,
            GENERIC_JOKE_HINTS,
        )
        patches = self.description.all_patches[self.players_config.player_index]
        hints_for_identifier = {
            identifier: exporter.create_message_for_hint(hint, False) for identifier, hint in patches.hints.items()
        }

        hints: dict[MapName, dict[EventNumber, CaverdataMapsHints]] = defaultdict(dict)

        for hint_node in self.game.region_list.iterate_nodes_of_type(HintNode):
            mapname = typing.cast(
                "MapName",
                hint_node.extra.get("event_map", self.game.region_list.nodes_to_area(hint_node).extra["map_name"]),
            )
            event = typing.cast("EventNumber", hint_node.extra["event"])

            hints[mapname][event] = {
                "text": hints_for_identifier[hint_node.identifier],
                "facepic": hint_node.extra.get("facepic", "0000"),
                "ending": "<NOD" + hint_node.extra.get("ending", "<END"),
            }

        return hints

    def _create_starting_script(self) -> str:
        # objective flags
        starting_script = self.configuration.objective.script
        # B2 falling blocks disable flag
        if self.configuration.no_blocks:
            starting_script += "<FL+1351"
        # rocket skip enabled
        if (
            self.configuration.trick_level.level_for_trick(self.game.resource_database.get_trick("Dboost")).as_number
            >= 4
        ):
            starting_script += "<FL+6400"
        # initialize HP counter
        starting_script += set_flag(4011, self.configuration.starting_hp, bits=6)
        # CMP mapflags: Camp, Labyrinth B, Jail no. 1, Grasstown, Outer Wall
        starting_script += "<MP+0040<MP+0043<MP+0057<MP+0006<MP+0053"
        # Softlock prevention mapflags
        starting_script += "<MP+0032<MP+0033<MP+0036"

        # unlock teleporter slots in the correct order
        starting_script += "<PS+0001:6001<PS+0002:6002<PS+0003:6003<PS+0004:6004<PS+0005:6005"

        # Starting Items
        starting_script += self._script_for_starting_items()

        # Starting Locations
        if self.patches.starting_location.area in {"Start Point", "First Cave", "Hermit Gunsmith"}:
            # started in first cave
            starting_script += "<FL+6200"
        else:
            # flags set during first cave in normal gameplay
            starting_script += "<FL+0301<FL+0302<FL+1641<FL+1642<FL+0320<FL+0321"
            waterway = {"Waterway", "Waterway Cabin", "Main Artery"}
            world_name, area_name = self.patches.starting_location.area_identifier.as_tuple
            if world_name == "Labyrinth" and area_name not in waterway:
                # started near camp; disable camp collision
                starting_script += "<FL+6202"
            elif (world_name != "Mimiga Village" and area_name not in waterway) or area_name == "Arthur's House":
                # started outside mimiga village
                starting_script += "<FL+6201"

        starting_script += self._tra_for_warp_to_start()

        return starting_script

    def _script_for_starting_items(self) -> str:
        self._equip_num = 0
        self._items_extra = ""
        self._trades = {
            "blade": 0,
            "fireball": 0,
            "keys": 0,
            "medals": 0,
            "lewd": 0,
            "sprinklers": 0,
            "mushrooms": 0,
            "none": 0,
        }
        self._life = 0

        self._starting_items = self.patches.starting_resources()

        starting_msg = self._grant_starting_items()

        if self._starting_items.num_resources > 0:
            starting_msg += self._items_extra

            if self._life > 0:
                starting_msg += (
                    f"<GIT1006Got a =Life Capsule=!<ML+{num_to_tsc_value(self._life).decode('utf-8')}\r\n"
                    f"Max health increased by\r\n"
                    f"{self._life}!<WAI0010<NOD\r\n<CLR"
                )

            if starting_msg:
                starting_msg += "<GIT0000\r\n"

            if self._trades["blade"] >= 2:
                starting_msg += (
                    "You may trade the =Nemesis=\r\n"
                    "with the =Blade= and vice-versa\r\n"
                    "at the computer in Arthur's House.<WAI0025<NOD<FL+2811\r\n<CLR"
                )

            if self._trades["fireball"] >= 2:
                starting_msg += (
                    "You may trade the =Fireball=\r\n"
                    "with the =Snake= and vice-versa\r\n"
                    "at the computer in Arthur's House.<WAI0025<NOD<FL+2802\r\n<CLR"
                )

            # Consolidation items
            if self._trades["keys"] >= 2:
                starting_msg += "<IT+0040"
            if self._trades["medals"] >= 2:
                starting_msg += "<IT+0041"
            if self._trades["lewd"] >= 2:
                starting_msg += "<IT+0042"
            if self._trades["sprinklers"] >= 2:
                starting_msg += "<IT+0043"
            if self._trades["mushrooms"] >= 2:
                starting_msg += "<IT+0044"

        starting_script = ""
        if starting_msg:
            starting_script += f"\r\n<PRI<MSG<TUR{starting_msg}<CLO"

        starting_script += f"<EQ+{num_to_tsc_value(self._equip_num).decode('utf-8')}\r\n"

        # Starting HP
        if self.configuration.starting_hp != 3 or self._life > 0:
            life = num_to_tsc_value(self.configuration.starting_hp + self._life - 3).decode("utf-8")
            starting_script += f"<ML+{life}"

        return starting_script

    def _grant_starting_items(self) -> str:
        starting_msg = ""
        self._missile = next(
            (res for res, _ in self._starting_items.as_resource_gain() if res.short_name in {"missile", "tempMissile"}),
            None,
        )
        for item, _ in self._starting_items.as_resource_gain():
            if item.resource_type != ResourceType.ITEM or item == self._missile:
                continue

            if item.short_name == "lifeCapsule":
                self._life = self._starting_items[item]
                continue

            if item.short_name == "puppies":
                num_puppies = self._starting_items[item]

                flags = "".join([f"<FL+{num_to_tsc_value(5001 + i).decode('utf-8')}" for i in range(num_puppies)])
                flags += "<FL+0274"
                if num_puppies == 5:
                    flags += "<FL+0593"

                words = {
                    1: "a =Puppy=",
                    2: "two =Puppies=",
                    3: "three =Puppies=",
                    4: "four =Puppies=",
                    5: "all five =Puppies=",
                }

                starting_msg += (
                    f"<IT+0014<GIT1014{flags}<SNP0136:0000:0000:0000\r\nGot {words[num_puppies]}!<WAI0010<NOD\r\n<CLR"
                )
                continue

            if item.extra.get("text") is None:
                raise ValueError(f"{item.long_name} is not a valid starting item!")

            item_num = item.extra.get("it+")
            arms_num = item.extra.get("am+")
            if (item_num is None) == (arms_num is None):
                raise ValueError(f"{item.long_name} must define exactly one of item_num and arms_num.")

            self._equip_num |= item.extra.get("equip", 0)
            self._items_extra += item.extra.get("extra", "")
            trade = item.extra.get("trade", "none")
            self._trades[trade] += 1

            if item_num is not None:
                git = num_to_tsc_value(item_num + 1000).decode("utf-8")
                plus = f"<IT+{num_to_tsc_value(item_num).decode('utf-8')}"
            elif arms_num is not None:
                if item.short_name in {"missiles", "supers"} and self._missile is not None:
                    ammo = num_to_tsc_value(self._starting_items[self._missile]).decode("utf-8")
                else:
                    ammo = num_to_tsc_value(item.extra.get("ammo", 0)).decode("utf-8")

                git = num_to_tsc_value(arms_num).decode("utf-8")
                plus = f"<AM+{num_to_tsc_value(arms_num).decode('utf-8')}:{ammo}"

            flag = num_to_tsc_value(item.extra["flag"]).decode("utf-8")
            text = item.extra["text"]

            starting_msg += f"<GIT{git}{plus}<FL+{flag}\r\n{text}<WAI0010<NOD\r\n<CLR"

            if self._trades[trade] >= 2:
                # we do this mid-loop, even though it duplicates them for the keys.
                # otherwise, starting with *everything* can cause some items to be
                # missed due to inventory overflow
                match trade:
                    case "keys":
                        starting_msg += "<IT-0001<IT-0003<IT-0009<IT-0010<IT-0017<IT-0025"
                    case "medals":
                        starting_msg += "<IT-0031<IT-0036"
                    case "lewd":
                        starting_msg += "<IT-0035<IT-0037"
                    case "sprinklers":
                        starting_msg += "<IT-0028<IT-0029"
                    case "mushrooms":
                        starting_msg += "<IT-0033<IT-0034"

        return starting_msg

    def _tra_for_warp_to_start(self) -> str:
        return typing.cast(
            "str",
            self.game.region_list.area_by_area_location(self.patches.starting_location.area_identifier).extra[
                "starting_script"
            ],
        )

    def _head_tsc_edits(self) -> dict[EventNumber, CaverdataOtherTsc]:
        # Configurable missile ammo
        small_missile_ammo = self.pickup_db.ammo_pickups["Missile Expansion"]
        hell_missile_ammo = self.pickup_db.ammo_pickups["Large Missile Expansion"]

        ammo_state = self.configuration.ammo_pickup_configuration.pickups_state
        small_missile = ammo_state[small_missile_ammo].ammo_count[0]
        hell_missile = ammo_state[hell_missile_ammo].ammo_count[0]
        base_missiles = self._starting_items[self._missile] if self._missile is not None else 0
        missile_id = "0005"
        supers_id = "0010"
        missile_events = {
            "0030": (missile_id, small_missile + base_missiles),  # normal launcher
            "0031": (missile_id, small_missile),  # normal expansion
            "0032": (supers_id, small_missile),  # supers expansion
            "0035": (missile_id, hell_missile + base_missiles),  # normal hell launcher
            "0036": (missile_id, hell_missile),  # normal hell expansion
            "0037": (supers_id, hell_missile),  # supers hell expansion
            "0038": (supers_id, base_missiles),  # supers launcher
        }
        head: dict[EventNumber, CaverdataOtherTsc] = {}
        for event, m_ammo in missile_events.items():
            head[event] = {
                "needle": "<AM%+....:....",
                "script": f"<AM+{m_ammo[0]}:{num_to_tsc_value(m_ammo[1]).decode('utf-8')}",
            }

        life_capsules = [
            ("Small Life Capsule", "0012"),
            ("Medium Life Capsule", "0013"),
            ("Large Life Capsule", "0014"),
        ]
        for name, event in life_capsules:
            amount = self.configuration.standard_pickup_configuration.pickups_state[
                self.pickup_db.standard_pickups[name]
            ].included_ammo[0]
            head[event] = {
                "needle": ".!<ML%+....",
                "script": f"{amount}!<ML+{num_to_tsc_value(amount).decode('utf-8')}",
            }

        return head
