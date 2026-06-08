from __future__ import annotations

import math
import textwrap
from collections import defaultdict
from typing import TYPE_CHECKING, override

from randovania.exporter.hints import credits_spoiler
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.exporter.pickup_exporter import ExportedPickupDetails
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.games.zero_mission.exporter.hint_namer import MZMHintNamer
from randovania.games.zero_mission.layout import MZMConfiguration, MZMCosmeticPatches
from randovania.generator.pickup_pool import pickup_creator

if TYPE_CHECKING:
    from mars_patcher.zm.auto_generated_types import MarsschemazmStartingItems

    from randovania.exporter.hints.hint_namer import HintNamer
    from randovania.exporter.patch_data_factory import PatcherDataMeta


class MZMPatchDataFactory(PatchDataFactory[MZMConfiguration, MZMCosmeticPatches]):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_ZERO_MISSION

    @override
    @classmethod
    def hint_namer_type(cls) -> type[HintNamer]:
        return MZMHintNamer

    def _create_starting_location(self) -> dict:
        # creates the data for the games starting location
        starting_location_node = self.game.region_list.node_by_identifier(self.patches.starting_location)
        starting_location_dict = {
            "area": self.game.region_list.nodes_to_region(starting_location_node).extra["area_id"],
            "room": self.game.region_list.nodes_to_area(starting_location_node).extra["room_id"][0],
            "block_x": starting_location_node.extra["X"],
            "block_y": starting_location_node.extra["Y"],
        }
        return starting_location_dict

    def _create_starting_items(self) -> MarsschemazmStartingItems:
        # creates the data for the games starting items
        starting_dict: MarsschemazmStartingItems = {
            "energy": self.configuration.energy_per_tank - 1,
            "abilities": [],
            "downloaded_maps": [0, 1, 2, 3, 4, 5, 6],
            "missiles": 0,
            "super_missiles": 0,
            "power_bombs": 0,
            "suit_type": "FULLY_POWERED",
            "ziplines_activated": False,
        }

        for item, quantity in self.patches.starting_resources().as_resource_gain():  # TODO update post #9153
            assert isinstance(item, ItemResourceInfo)

            match item.extra["StartingItemCategory"]:
                case "Missiles":
                    starting_dict["missiles"] += quantity
                case "SuperMissiles":
                    starting_dict["super_missiles"] += quantity
                case "PowerBombs":
                    starting_dict["power_bombs"] += quantity
                case "Energy":
                    starting_dict["energy"] += self.configuration.energy_per_tank * quantity
                case "Abilities":
                    starting_dict["abilities"].append(item.extra["StartingItemName"])
                case "Ziplines":
                    starting_dict["ziplines_activated"] = True
                case _:
                    raise ValueError(f"{item.extra['StartingItemCategory']} is unsupported as starting")

        return starting_dict

    def _create_pickup_dict(self, pickup_list: list[ExportedPickupDetails]) -> dict:
        # creates the data for major and minor locations
        pickup_map_dict = {}
        minor_pickup_list = []
        major_pickup_list = []

        for pickup in pickup_list:
            node = self.game.region_list.node_from_pickup_index(pickup.index)
            is_major = False
            jingle = "MINOR"
            if "source" in node.extra:
                is_major = True
            if not pickup.is_for_remote_player and pickup.conditional_resources[0].resources:
                conditional_extras = pickup.conditional_resources[0].resources[-1][0].extra
                resource = conditional_extras["item"]
                jingle = conditional_extras.get("Jingle", "MINOR")
            else:
                resource = "NONE"

            sprite = pickup.model.name

            if is_major:
                major_pickup = {
                    "source": node.extra["source"],
                    "item": resource,
                    "item_sprite": sprite,
                    "jingle": jingle,
                }
                major_pickup_list.append(major_pickup)
            else:
                minor_pickup = {
                    "area": self.game.region_list.nodes_to_region(node).extra["area_id"],
                    "room": self.game.region_list.nodes_to_area(node).extra["room_id"][0],
                    "block_x": node.extra["blockx"],
                    "block_y": node.extra["blocky"],
                    "item": resource,
                    "item_sprite": sprite,
                    "jingle": jingle,
                }
                minor_pickup_list.append(minor_pickup)
        pickup_map_dict = {"major_locations": major_pickup_list, "minor_locations": minor_pickup_list}

        return pickup_map_dict

    def _create_tank_increments(self) -> dict:
        # creates the data for the amount of ammo each relevant resource type provides
        tank_dict = {}
        for ammo_definition, ammo_state in self.patches.configuration.ammo_pickup_configuration.pickups_state.items():
            tank_dict[ammo_definition.extra["TankIncrementName"]] = ammo_state.ammo_count[0]
        tank_dict["energy_tank"] = self.configuration.energy_per_tank

        for stand_definition, stand_state in self.configuration.standard_pickup_configuration.pickups_state.items():
            if "LauncherIncrementName" in stand_definition.extra:
                tank_dict[stand_definition.extra["LauncherIncrementName"]] = stand_state.included_ammo[0]
        return tank_dict

    def _create_title_text(self) -> list:
        # creates the data for the title text, this is further modified in the game_exporter
        elements = []
        for line, word in enumerate(self.description.shareable_word_hash.split(), 12):
            final_word = word if len(word) <= 30 else f"{word[0:27]}..."
            elements.append({"line_num": line, "text": final_word.center(30)})
        return elements

    # def _create_intro_text(self) -> list:
    # TODO
    #     elements = []
    #
    #     return elements

    def _credits_elements(self) -> defaultdict[str, list[dict]]:
        # creates the credits elements for each pickup
        elements = defaultdict(list)
        majors = credits_spoiler.generic_credits(
            self.configuration.standard_pickup_configuration, self.description.all_patches, self.players_config
        )

        for pickup, locations in majors:
            for location in locations:
                # Special case for special messages
                if isinstance(location, str):
                    elements[pickup.name].append({"World": None, "Region": "", "Area": location})
                    continue

                region_list = default_database.game_description_for(location.location.game).region_list
                pickup_node = region_list.node_from_pickup_index(location.location.location)
                elements[pickup.name].append(
                    {
                        "World": location.world_name,
                        "Region": pickup_node.identifier.region,
                        "Area": pickup_node.identifier.area,
                    }
                )
        return elements

    @staticmethod
    def _wrap_text_for_credits(text: str) -> list[str]:
        return textwrap.wrap(text, width=30)

    def _create_credits_text(self) -> list:
        # creates the data for the credits lines
        credits_array = []
        spoiler_dict = self._credits_elements()

        major_pickup_name_order = {
            pickup.name: index
            for index, pickup in enumerate(self.configuration.standard_pickup_configuration.pickups_state.keys())
        }

        def sort_pickup(p: str) -> tuple[int | float, str]:
            return major_pickup_name_order.get(p, math.inf), p

        credits_array.append({"line_type": "WHITE_BIG", "text": "Item Locations", "blank_lines": 2})

        for pickup in sorted(spoiler_dict.keys(), key=sort_pickup):
            credits_array.append({"line_type": "RED", "text": pickup, "blank_lines": 1})
            for location in spoiler_dict[pickup]:
                region_name = location["Region"]
                area_name = location["Area"]
                # We want to avoid displaying something like "s3 - s3 blabla", so remove possible redundancies like that
                # Also need to ignore the case of random starting items where region name is blank
                if area_name.startswith(region_name) and region_name != "":
                    area_name = area_name[len(region_name) + 1 :]
                world_name = location["World"] if location["World"] else ""

                region_lines = self._wrap_text_for_credits(region_name)
                area_lines = self._wrap_text_for_credits(area_name)
                world_lines = self._wrap_text_for_credits(world_name)
                for line in world_lines:
                    credits_array.append({"line_type": "BLUE", "text": line, "blank_lines": 0})
                for line in region_lines:
                    credits_array.append({"line_type": "WHITE", "text": line, "blank_lines": 0})
                for line in area_lines:
                    credits_array.append({"line_type": "WHITE", "text": line, "blank_lines": 0})
                credits_array[-1]["blank_lines"] = 1

        # Have last item give more space
        credits_array[-1]["blank_lines"] = 3

        # Self plug, for streaming/showcasing.
        credits_array.append({"line_type": "BLUE", "text": "Play this Randomizer at", "blank_lines": 0})
        credits_array.append({"line_type": "WHITE", "text": "randovania.org", "blank_lines": 3})

        return credits_array

    def _create_room_names(self) -> list[dict]:
        # creates the data for the room names
        names = []
        for region in self.game.region_list.regions:
            for area in region.areas:
                for number in area.extra["room_id"]:
                    names.append(
                        {
                            "area": region.extra["area_id"],
                            "room": number,
                            "name": area.name,
                        }
                    )
        return names

    def create_useless_pickup(self) -> PickupEntry:
        """Used for any location with no PickupEntry assigned to it."""
        return pickup_creator.create_nothing_pickup(
            self.game.get_resource_database_view(),
            model_name="EMPTY",
        )

    def create_visual_nothing(self) -> PickupEntry:
        return pickup_creator.create_visual_nothing(self.game_enum(), "ANONYMOUS")

    def create_game_specific_data(self, randovania_meta: PatcherDataMeta) -> dict:
        pickup_list = self.export_pickup_list()
        mars_data = {
            "seed_hash": self.description.shareable_hash,
            "starting_location": self._create_starting_location(),
            "starting_items": self._create_starting_items(),
            "locations": self._create_pickup_dict(pickup_list),
            "tank_increments": self._create_tank_increments(),
            # "intro_text": self._create_intro_text(),
            "title_text": self._create_title_text(),
            "credits_text": self._create_credits_text(),
            "disable_demos": True,
            "remove_cutscenes": True,
            "fast_item_grab": True,
            "skip_door_transitions": False,
            "reveal_hidden_tiles": True,
            "room_names": self._create_room_names(),
            "accessibility_patches": True,
            "stereo_default": True,
            "disable_music": False,
            "disable_sound_effects": False,
        }
        # Uncomment to spew the patch data into the terminal
        import json

        print(json.dumps(mars_data))

        return mars_data
