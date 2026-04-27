from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.exporter.pickup_exporter import ExportedPickupDetails
from randovania.game.game_enum import RandovaniaGame
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
        starting_location_node = self.game.region_list.node_by_identifier(self.patches.starting_location)
        starting_location_dict = {
            "area": self.game.region_list.nodes_to_region(starting_location_node).extra["area_id"],
            "room": self.game.region_list.nodes_to_area(starting_location_node).extra["room_id"][0],
            "block_x": starting_location_node.extra["X"],
            "block_y": starting_location_node.extra["Y"],
        }
        return starting_location_dict

    def _create_starting_items(self) -> MarsschemazmStartingItems:
        starting_dict: MarsschemazmStartingItems = {
            "energy": self.configuration.energy_per_tank - 1,
            "abilities": [],
            "downloaded_maps": [0, 1, 2, 3, 4, 5, 6],
            "missiles": 0,
            "super_missiles": 0,
            "power_bombs": 0,
            "suit_type": "FULLY_POWERED",
            "ziplines_activated": self.configuration.starting_ziplines,
        }

        for item, quantity in self.patches.starting_resources().as_resource_gain():
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
                case _:
                    raise ValueError(f"{item.extra['StartingItemCategory']} is unsupported as starting")

        return starting_dict

    def _create_pickup_dict(self, pickup_list: list[ExportedPickupDetails]) -> dict:
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

            item_message = {}

            if is_major:
                major_pickup = {
                    "source": node.extra["source"],
                    "item": resource,
                    "item_sprite": sprite,
                    "jingle": jingle,
                }
                if item_message:
                    major_pickup["ItemMessages"] = item_message
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
                if item_message:
                    minor_pickup["ItemMessages"] = item_message
                minor_pickup_list.append(minor_pickup)
        pickup_map_dict = {"major_locations": major_pickup_list, "minor_locations": minor_pickup_list}

        return pickup_map_dict

    def _create_tank_increments(self) -> dict:
        tank_dict = {}
        for ammo_definition, ammo_state in self.patches.configuration.ammo_pickup_configuration.pickups_state.items():
            tank_dict[ammo_definition.extra["TankIncrementName"]] = ammo_state.ammo_count[0]
        tank_dict["energy_tank"] = self.configuration.energy_per_tank

        for stand_definition, stand_state in self.configuration.standard_pickup_configuration.pickups_state.items():
            if "LauncherIncrementName" in stand_definition.extra:
                tank_dict[stand_definition.extra["LauncherIncrementName"]] = stand_state.included_ammo[0]
        return tank_dict

    def _create_title_text(self) -> list:
        elements = []
        for line, word in enumerate(self.description.shareable_word_hash.split(), 12):
            final_word = word if len(word) <= 30 else f"{word[0:27]}..."
            elements.append({"LineNum": line, "Text": final_word.center(30)})
        return elements

    # def _create_intro_text(self) -> list:
    #     elements = []
    #
    #     return elements

    # def _create_credits_text(self) -> list:
    #     elements = []
    #
    #     return elements

    def _create_room_names(self) -> list[dict]:
        names = []
        for region in self.game.region_list.regions:
            for area in region.areas:
                for number in area.extra["room_id"]:
                    names.append(
                        {
                            "Area": region.extra["area_id"],
                            "Room": number,
                            "Name": area.name,
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
            # "credits_text": self._create_credits_text(),
            "disable_demos": False,
            "skip_door_transitions": False,
            "unexplored_map": False,
            "RoomNames": self._create_room_names(),
            "accessibility_patches": True,
            "stereo_default": True,
            "disable_music": False,
            "disable_sound_effects": False,
        }
        # Uncomment to spew the patch data into the terminal
        import json

        print(json.dumps(mars_data))

        return mars_data
