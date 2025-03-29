from __future__ import annotations

import math
import typing
from collections import defaultdict
from typing import TYPE_CHECKING, override

from randovania.exporter import item_names
from randovania.exporter.hints import credits_spoiler, guaranteed_item_hint
from randovania.exporter.hints.hint_exporter import HintExporter
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.db.hint_node import HintNode
from randovania.games.fusion.exporter.hint_namer import FusionColor, FusionHintNamer
from randovania.games.fusion.exporter.joke_hints import FUSION_JOKE_HINTS
from randovania.games.fusion.layout.fusion_configuration import FusionConfiguration
from randovania.games.fusion.layout.fusion_cosmetic_patches import FusionCosmeticPatches
from randovania.generator.pickup_pool import pickup_creator
from randovania.layout.base.hint_configuration import SpecificPickupHintMode
from randovania.layout.base.pickup_model import PickupModelStyle
from randovania.lib import json_lib

if TYPE_CHECKING:
    from mars_patcher.auto_generated_types import MarsschemaStartingitems

    from randovania.exporter.pickup_exporter import ExportedPickupDetails
    from randovania.game_description.pickup.pickup_entry import PickupEntry


class FusionPatchDataFactory(PatchDataFactory[FusionConfiguration, FusionCosmeticPatches]):
    _placeholder_metroid_message = "placeholder metroid text"
    _lang_list = ["JapaneseKanji", "JapaneseHiragana", "English", "German", "French", "Italian", "Spanish"]
    _easter_egg_bob = 64
    _easter_egg_shiny = 1024

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.FUSION

    @override
    @classmethod
    def hint_namer_type(cls) -> type[FusionHintNamer]:
        return FusionHintNamer

    def _create_pickup_dict(self, pickup_list: list[ExportedPickupDetails]) -> dict:
        pickup_map_dict = {}
        minor_pickup_list = []
        major_pickup_list = []
        for pickup in pickup_list:
            node = self.game.region_list.node_from_pickup_index(pickup.index)
            is_major = False
            if "source" in node.extra:
                is_major = True
            if not pickup.is_for_remote_player and pickup.conditional_resources[0].resources:
                resource = pickup.conditional_resources[0].resources[-1][0].extra["item"]
            else:
                resource = "None"

            text = pickup.collection_text[0]
            sprite = pickup.model.name

            custom_message = {}
            # Special case where we ignore metroid dna right now, because that needs more patcher work.
            if text != self._placeholder_metroid_message:
                custom_message = {"Languages": dict.fromkeys(self._lang_list, text)}

            # Shiny easter eggs
            if (
                not pickup.is_for_remote_player
                and self.configuration.pickup_model_style == PickupModelStyle.ALL_VISIBLE
            ):
                if (
                    pickup.index.index == 43
                    and resource == "MissileTank"
                    and self.rng.randint(0, self._easter_egg_bob) == 0
                ):
                    sprite = "ShinyMissileTank"
                    custom_message = {"Languages": dict.fromkeys(self._lang_list, "Bob acquired.\nHe says hi to you.")}

                if resource == "PowerBombTank" and self.rng.randint(0, self._easter_egg_shiny) == 0:
                    sprite = "ShinyPowerBombTank"
                    custom_message = {"Languages": dict.fromkeys(self._lang_list, "Shiny Power Bomb Tank acquired.")}

            if is_major:
                major_pickup = {
                    "Source": node.extra["source"],
                    "Item": resource,
                }
                if custom_message:
                    major_pickup["ItemMessages"] = custom_message
                major_pickup_list.append(major_pickup)
            else:
                minor_pickup = {
                    "Area": self.game.region_list.nodes_to_region(node).extra["area_id"],
                    "Room": self.game.region_list.nodes_to_area(node).extra["room_id"][0],
                    "BlockX": node.extra["blockx"],
                    "BlockY": node.extra["blocky"],
                    "Item": resource,
                    "ItemSprite": sprite,
                }
                if custom_message:
                    minor_pickup["ItemMessages"] = custom_message
                minor_pickup_list.append(minor_pickup)
        pickup_map_dict = {"MajorLocations": major_pickup_list, "MinorLocations": minor_pickup_list}
        return pickup_map_dict

    def _create_starting_location(self) -> dict:
        starting_location_node = self.game.region_list.node_by_identifier(self.patches.starting_location)
        starting_location_dict = {
            "Area": self.game.region_list.nodes_to_region(starting_location_node).extra["area_id"],
            "Room": self.game.region_list.nodes_to_area(starting_location_node).extra["room_id"][0],
            "BlockX": starting_location_node.extra["X"],
            "BlockY": starting_location_node.extra["Y"],
        }
        return starting_location_dict

    def _create_starting_items(self) -> MarsschemaStartingitems:
        starting_dict: MarsschemaStartingitems = {
            "Energy": self.configuration.energy_per_tank - 1,
            "Abilities": [],
            "SecurityLevels": [],
            "DownloadedMaps": [0, 1, 2, 3, 4, 5, 6],
        }
        missile_launcher = next(
            state
            for defi, state in self.configuration.standard_pickup_configuration.pickups_state.items()
            if defi.name == "Missile Launcher Data"
        )
        # Fusion always starts with launchers ammo, even if launcher is not a starting item
        starting_dict["Missiles"] = missile_launcher.included_ammo[0]

        pb_launcher = next(
            state
            for defi, state in self.configuration.standard_pickup_configuration.pickups_state.items()
            if defi.name == "Power Bomb Data"
        )
        starting_dict["PowerBombs"] = pb_launcher.included_ammo[0]

        for item, quantity in self.patches.starting_resources().as_resource_gain():
            match item.extra["StartingItemCategory"]:
                case "Missiles" | "PowerBombs" | "Metroids":
                    continue
                case "Energy":
                    starting_dict["Energy"] += self.configuration.energy_per_tank * quantity
                case "SecurityLevels":
                    starting_dict["SecurityLevels"].append(item.extra["StartingItemName"])
                case "Abilities":
                    starting_dict["Abilities"].append(item.extra["StartingItemName"])
                case _:
                    raise ValueError(f"{item.extra['StartingItemCategory']} is unsupported as starting")

        return starting_dict

    def _create_tank_increments(self) -> dict:
        tank_dict = {}
        for definition, state in self.patches.configuration.ammo_pickup_configuration.pickups_state.items():
            tank_dict[definition.extra["TankIncrementName"]] = state.ammo_count[0]
        tank_dict["EnergyTank"] = self.configuration.energy_per_tank
        return tank_dict

    def _create_door_locks(self) -> list[dict]:
        result = []
        for node, weakness in self.patches.all_dock_weaknesses():
            for id in node.extra["door_idx"]:
                result.append(
                    {
                        "Area": self.game.region_list.nodes_to_region(node).extra["area_id"],
                        "Door": id,
                        "LockType": weakness.extra["type"],
                    }
                )
        return result

    def _create_palette(self) -> dict:
        cosmetics = self.cosmetic_patches
        palettes = {}

        palette_type_dict = {
            "suit": "Samus",
            "beam": "Beams",
            "enemy": "Enemies",
            "tileset": "Tilesets",
        }

        for attr_name, palettes_key in palette_type_dict.items():
            if getattr(cosmetics, f"enable_{attr_name}_palette"):
                palettes[palettes_key] = {
                    "HueMin": getattr(cosmetics, f"{attr_name}_hue_min"),
                    "HueMax": getattr(cosmetics, f"{attr_name}_hue_max"),
                }
        palette_dict = {
            "Seed": self.description.get_seed_for_world(self.players_config.player_index),
            "Randomize": palettes,
            "ColorSpace": cosmetics.color_space.long_name,
        }
        return palette_dict

    def _create_nav_text(self) -> dict:
        nav_text_json = {}
        namer = FusionHintNamer(self.description.all_patches, self.players_config)
        exporter = HintExporter(namer, self.rng, FUSION_JOKE_HINTS)

        artifacts = [self.game.resource_database.get_item(f"Infant Metroid {i + 1}") for i in range(20)]

        metroid_precision = self.configuration.hints.specific_pickup_hints["artifacts"]
        charge_precision = self.configuration.hints.specific_pickup_hints["charge_beam"]

        if metroid_precision != SpecificPickupHintMode.DISABLED:
            metroid_hint_mapping = guaranteed_item_hint.create_guaranteed_hints_for_resources(
                self.description.all_patches,
                self.players_config,
                namer,
                True if metroid_precision == SpecificPickupHintMode.HIDE_AREA else False,
                artifacts,
                True,
            )
        if charge_precision != SpecificPickupHintMode.DISABLED:
            charge_hint_mapping = guaranteed_item_hint.create_guaranteed_hints_for_resources(
                self.description.all_patches,
                self.players_config,
                namer,
                True if charge_precision == SpecificPickupHintMode.HIDE_AREA else False,
                [self.game.resource_database.get_item("ChargeBeam")],
                True,
            )

        hints = {}

        for node in self.game.region_list.iterate_nodes_of_type(HintNode):
            hint_location = node.extra["hint_name"]
            if hint_location == "AuxiliaryPower" and charge_precision != SpecificPickupHintMode.DISABLED:
                hints[hint_location] = " ".join(
                    [text for _, text in charge_hint_mapping.items() if "has no need to be located" not in text]
                )
            elif hint_location == "RestrictedLabs" and metroid_precision != SpecificPickupHintMode.DISABLED:
                hints[hint_location] = " ".join(
                    [text for _, text in metroid_hint_mapping.items() if "has no need to be located" not in text]
                )
            else:
                hints[hint_location] = exporter.create_message_for_hint(
                    self.patches.hints[node.identifier],
                    True,
                ).strip()

        starting_items_list = item_names.additional_starting_equipment(
            self.patches.configuration, self.patches.game, self.patches
        )
        starting_items_text = (
            f"Starting items: {(', '.join(starting_items_list))}. "
            if self.configuration.short_intro_text
            else f"HQ has provided you with the following starting items: {(', '.join(starting_items_list))}. "
        )
        if len(starting_items_list) == 0:
            starting_items_text = ""
        metroid_location_text = "anywhere" if self.configuration.artifacts.prefer_anywhere else "at bosses"
        colorize_text = FusionHintNamer.colorize_text
        long_intro = (
            f"{starting_items_text}Your objective is as follows: the {colorize_text(FusionColor.YELLOW, 'SA-X', True)} "
            f"has discovered and destroyed a top secret {colorize_text(FusionColor.YELLOW, 'Metroid', True)} "
            f"breeding facility. It released {self.configuration.artifacts.placed_artifacts} "
            "infant Metroids into the station. "
            f"Initial scans indicate that they are hiding {metroid_location_text}. "
            f"Find and capture {self.configuration.artifacts.required_artifacts} of them, "
            "to lure out the SA-X. "
            "Then initiate the station's self-destruct sequence. "
            f"Uplink at {colorize_text(FusionColor.PINK, 'Navigation Rooms', True)} along the way. "
            "I can scan the station for useful equipment from there.[OBJECTIVE]Good. Move out."
        )
        short_intro = (
            f"{starting_items_text}"
            f"{
                (
                    (
                        f'Gather {self.configuration.artifacts.required_artifacts}/'
                        f'{self.configuration.artifacts.placed_artifacts} Infant Metroids hiding '
                        f'{metroid_location_text} to lure out the '
                        f'{colorize_text(FusionColor.YELLOW, "SA-X", True)} and prepare for battle.'
                    )
                    if self.configuration.artifacts.required_artifacts > 0
                    else f'Equip yourself to battle the {colorize_text(FusionColor.YELLOW, "SA-X", True)}.'
                )
            }"
        )
        for lang in self._lang_list:
            nav_text_json[lang] = {
                "NavigationTerminals": hints,
                "ShipText": {
                    "InitialText": short_intro if self.configuration.short_intro_text else long_intro,
                    "ConfirmText": "Any Objections, Lady?",
                },
            }
        return nav_text_json

    def _credits_elements(self) -> defaultdict[str, list[dict]]:
        elements = defaultdict(list)
        majors = credits_spoiler.get_locations_for_major_pickups_and_keys(
            self.description.all_patches, self.players_config
        )

        for pickup, locations in majors.items():
            for location in locations:
                region_list = default_database.game_description_for(location.location.game).region_list
                pickup_node = region_list.node_from_pickup_index(location.location.location)
                elements[pickup.name].append(
                    {
                        "World": location.world_name,
                        "Region": region_list.region_name_from_node(pickup_node),
                        "Area": region_list.nodes_to_area(pickup_node).name,
                    }
                )
        return elements

    def _create_credits_text(self) -> list:
        credits_array = []
        spoiler_dict = self._credits_elements()

        major_pickup_name_order = {
            pickup.name: index
            for index, pickup in enumerate(self.configuration.standard_pickup_configuration.pickups_state.keys())
        }

        def sort_pickup(p: str) -> tuple[int | float, str]:
            return major_pickup_name_order.get(p, math.inf), p

        for pickup in sorted(spoiler_dict.keys(), key=sort_pickup):
            credits_array.append({"LineType": "Red", "Text": pickup, "BlankLines": 1})
            for location in spoiler_dict[pickup]:
                if location["World"] is not None:
                    credits_array.append({"LineType": "Blue", "Text": location["World"], "BlankLines": 0})
                credits_array.append({"LineType": "White1", "Text": location["Region"], "BlankLines": 0})
                credits_array.append({"LineType": "White1", "Text": location["Area"], "BlankLines": 1})

        return credits_array

    def _create_nav_locks(self) -> dict:
        locks = {
            "MainDeckWest": "RED",
            "MainDeckEast": "BLUE",
            "OperationsDeck": "GREY",
            "Sector1Entrance": "GREEN",
            "Sector2Entrance": "GREEN",
            "Sector3Entrance": "YELLOW",
            "Sector4Entrance": "YELLOW",
            "Sector5Entrance": "RED",
            "Sector6Entrance": "RED",
            "AuxiliaryPower": "OPEN",
            "RestrictedLabs": "OPEN",
        }
        return locks

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

    def create_memo_data(self) -> dict:
        """Used to generate pickup collection messages."""
        memo_data: dict = typing.cast(
            "dict", json_lib.read_path(RandovaniaGame.FUSION.data_path.joinpath("pickup_database", "memo_data.json"))
        )

        for i in range(1, 21):
            memo_data[f"Infant Metroid {i}"] = memo_data["Infant Metroid"]

        memo_data["Missiles"] = memo_data["Missile Tank"]
        memo_data["Power Bombs"] = memo_data["Power Bomb Tank"]
        memo_data["EnergyTransferModule"] = memo_data["Nothing"]
        memo_data["Energy Tank"] = memo_data["Energy Tank"].format(Energy=self.configuration.energy_per_tank)

        return memo_data

    def create_useless_pickup(self) -> PickupEntry:
        """Used for any location with no PickupEntry assigned to it."""
        return pickup_creator.create_nothing_pickup(
            self.game.resource_database,
            model_name="Empty",
        )

    def create_visual_nothing(self) -> PickupEntry:
        """The model of this pickup replaces the model of all pickups when PickupModelDataSource is ETM"""
        return pickup_creator.create_visual_nothing(self.game_enum(), "Anonymous")

    def create_game_specific_data(self) -> dict:
        pickup_list = self.export_pickup_list()

        mars_data = {
            "SeedHash": self.description.shareable_hash,
            "StartingLocation": self._create_starting_location(),
            "StartingItems": self._create_starting_items(),
            "Locations": self._create_pickup_dict(pickup_list),
            "RequiredMetroidCount": self.configuration.artifacts.required_artifacts,
            "TankIncrements": self._create_tank_increments(),
            "MissileLimit": 3,
            "DoorLocks": self._create_door_locks(),
            "HideDoorsOnMinimap": self.configuration.dock_rando.is_enabled(),
            "Palettes": self._create_palette(),
            "NavigationText": self._create_nav_text(),
            "NavStationLocks": self._create_nav_locks(),
            "CreditsText": self._create_credits_text(),
            "DisableDemos": True,
            "RoomNames": self._create_room_names(),
            "AntiSoftlockRoomEdits": self.configuration.anti_softlock,
            "PowerBombsWithoutBombs": True,
            "SkipDoorTransitions": self.configuration.instant_transitions,
            "UnexploredMap": self.cosmetic_patches.starting_map,
            "RevealHiddenTiles": self.cosmetic_patches.reveal_blocks,
            "StereoDefault": self.cosmetic_patches.stereo_default,
            "DisableMusic": self.cosmetic_patches.disable_music,
            "DisableSoundEffects": self.cosmetic_patches.disable_sfx,
        }
        ## Uncomment to spew the patch data into the terminal
        # import json
        # print(json.dumps(mars_data))

        return mars_data
