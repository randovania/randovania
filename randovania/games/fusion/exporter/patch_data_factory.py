from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter import item_names, pickup_exporter
from randovania.exporter.hints import guaranteed_item_hint
from randovania.exporter.hints.hint_exporter import HintExporter
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.hint_node import HintNode
from randovania.games.fusion.exporter.hint_namer import FusionHintNamer
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pickup_creator

if TYPE_CHECKING:
    from randovania.exporter.pickup_exporter import ExportedPickupDetails
    from randovania.games.fusion.layout.fusion_configuration import FusionConfiguration
    from randovania.games.fusion.layout.fusion_cosmetic_patches import FusionCosmeticPatches


class FusionPatchDataFactory(PatchDataFactory):
    cosmetic_patches: FusionCosmeticPatches
    configuration: FusionConfiguration

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.FUSION

    def _create_pickup_dict(self, pickup_list: list[ExportedPickupDetails]) -> dict:
        pickup_map_dict = {}
        minor_pickup_list = []
        major_pickup_list = []
        for pickup in pickup_list:
            node = self.game.region_list.node_from_pickup_index(pickup.index)
            is_major = False
            if "source" in node.extra:
                is_major = True

            resource = (
                pickup.conditional_resources[0].resources[-1][0].extra["item"] if not pickup.other_player else "None"
            )
            if is_major:
                major_pickup_list.append({"Source": node.extra["source"], "Item": resource})
            else:
                minor_pickup_list.append(
                    {
                        "Area": self.game.region_list.nodes_to_region(node).extra["area_id"],
                        "Room": self.game.region_list.nodes_to_area(node).extra["room_id"][0],
                        "BlockX": node.extra["blockx"],
                        "BlockY": node.extra["blocky"],
                        "Item": resource,
                        "ItemSprite": pickup.model.name,
                    }
                )
        pickup_map_dict = {"MajorLocations": major_pickup_list, "MinorLocations": minor_pickup_list}
        return pickup_map_dict

    def _create_starting_location(self) -> dict:
        starting_location_node = self.game.region_list.node_by_identifier(self.patches.starting_location)
        starting_location_dict = {
            "Area": self.game.region_list.nodes_to_region(starting_location_node).extra["area_id"],
            "Room": self.game.region_list.nodes_to_area(starting_location_node).extra["room_id"][0],
            "X": starting_location_node.extra["X"],
            "Y": starting_location_node.extra["Y"],
        }
        return starting_location_dict

    def _create_starting_items(self) -> dict:
        starting_dict = {
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
        starting_dict["Missiles"] = missile_launcher.included_ammo[0]
        pb_launcher = next(
            state
            for defi, state in self.configuration.standard_pickup_configuration.pickups_state.items()
            if defi.name == "Power Bomb Data"
        )
        starting_dict["PowerBombs"] = pb_launcher.included_ammo[0]

        for item in self.patches.starting_equipment:
            if "Metroid" in item.name:
                continue
            pickup_def = next(
                value for key, value in self.pickup_db.standard_pickups.items() if value.name == item.name
            )
            category = pickup_def.extra["StartingItemCategory"]
            # Special Case for E-Tanks
            if category == "Energy":
                starting_dict[category] += self.configuration.energy_per_tank
                continue
            starting_dict[category].append(pickup_def.extra["StartingItemName"])
        return starting_dict

    def _create_tank_increments(self) -> dict:
        tank_dict = {}
        for definition, state in self.patches.configuration.ammo_pickup_configuration.pickups_state.items():
            tank_dict[definition.extra["TankIncrementName"]] = state.ammo_count[0]
        tank_dict["EnergyTank"] = self.configuration.energy_per_tank
        return tank_dict

    def _create_door_locks(self):
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
        # TODO make this cleaner
        if cosmetics.enable_suit_palette:
            palettes["Samus"] = {
                "HueMin": cosmetics.suit_hue_min,
                "HueMax": cosmetics.suit_hue_max,
            }
        if cosmetics.enable_beam_palette:
            palettes["Beams"] = {
                "HueMin": cosmetics.beam_hue_min,
                "HueMax": cosmetics.beam_hue_max,
            }
        if cosmetics.enable_enemy_palette:
            palettes["Enemies"] = {"HueMin": cosmetics.enemy_hue_min, "HueMax": cosmetics.enemy_hue_max}
        if cosmetics.enable_tileset_palette:
            palettes["Tilesets"] = {
                "HueMin": cosmetics.tileset_hue_min,
                "HueMax": cosmetics.tileset_hue_max,
            }

        palette_dict = {
            "Randomize": palettes,
            "ColorSpace": cosmetics.color_space.long_name,
        }
        return palette_dict

    def _create_nav_text(self) -> dict:
        nav_text_json = {}
        hint_lang_list = ["JapaneseKanji", "JapaneseHiragana", "English", "German", "French", "Italian", "Spanish"]
        namer = FusionHintNamer(self.description.all_patches, self.players_config)
        exporter = HintExporter(namer, self.rng, ["A joke hint."])

        artifacts = [self.game.resource_database.get_item(f"Infant Metroid {i + 1}") for i in range(20)]

        metroid_hint_mapping = guaranteed_item_hint.create_guaranteed_hints_for_resources(
            self.description.all_patches,
            self.players_config,
            FusionHintNamer(self.description.all_patches, self.players_config),
            False,  # TODO: make this depending on hint settings later:tm:
            artifacts,
            True,
        )

        hints = {}
        for node in self.game.region_list.iterate_nodes():
            if not isinstance(node, HintNode):
                continue
            hints[node.extra["hint_name"]] = exporter.create_message_for_hint(
                self.patches.hints[self.game.region_list.identifier_for_node(node)],
                self.description.all_patches,
                self.players_config,
                True,
            ).strip()
            if node.extra["hint_name"] == "RestrictedLabs":
                hints[node.extra["hint_name"]] = " ".join(
                    [text for _, text in metroid_hint_mapping.items() if "has no need to be located" not in text]
                )

        starting_items_list = item_names.additional_starting_equipment(
            self.patches.configuration, self.patches.game, self.patches
        )
        starting_items_text = (
            "HQ has provided you with the following starting items: " + ", ".join(starting_items_list) + ". "
            if len(starting_items_list) > 0
            else ""
        )
        metroid_location_text = "anywhere" if self.configuration.artifacts.prefer_anywhere else "at bosses"
        for lang in hint_lang_list:
            nav_text_json[lang] = {
                "NavigationTerminals": hints,
                "ShipText": {
                    "InitialText": (
                        f"{starting_items_text}Your objective is as follows: the [COLOR=3]SA-X[/COLOR] "
                        f"has discovered and destroyed a top secret [COLOR=3]Metroid[/COLOR] breeding facility. "
                        f"It released {self.patches.configuration.artifacts.placed_artifacts} "
                        "infant Metroids into the station. "
                        f"Initial scans indicate that they are hiding {metroid_location_text}. "
                        f"Find and capture {self.patches.configuration.artifacts.required_artifacts} of them, "
                        "to lure out the SA-X. "
                        "Then initiate the station's self-destruct sequence. "
                        "Uplink at [COLOR=2]Navigation Rooms[/COLOR] along the way. "
                        "I can scan the station for useful equipment from there.[OBJECTIVE]Good. Move out."
                    ),
                    "ConfirmText": "Any Objections, Lady?",
                },
            }
        return nav_text_json

    def create_data(self) -> dict:
        db = self.game

        useless_target = PickupTarget(
            pickup_creator.create_nothing_pickup(db.resource_database, "Empty"), self.players_config.player_index
        )

        pickup_list = pickup_exporter.export_all_indices(
            self.patches,
            useless_target,
            self.game.region_list,
            self.rng,
            self.configuration.pickup_model_style,
            self.configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(
                pickup_exporter.GenericAcquiredMemo(), self.players_config, self.game_enum()
            ),
            visual_nothing=pickup_creator.create_visual_nothing(self.game_enum(), "Anonymous"),
        )

        mars_data = {
            "SeedHash": self.description.shareable_hash,
            "StartingLocation": self._create_starting_location(),
            "StartingItems": self._create_starting_items(),
            "Locations": self._create_pickup_dict(pickup_list),
            "RequiredMetroidCount": self.configuration.artifacts.required_artifacts,
            "TankIncrements": self._create_tank_increments(),
            "DoorLocks": self._create_door_locks(),
            "SkipDoorTransitions": self.configuration.instant_transitions,
            "Palettes": self._create_palette(),
            "NavigationText": self._create_nav_text(),
        }
        import json

        foo = json.dumps(mars_data)
        print(foo)
        return {}
