from __future__ import annotations

import typing
from random import Random
from typing import TYPE_CHECKING, override

from randovania import monitoring
from randovania.exporter import item_names
from randovania.exporter.hints import credits_spoiler, guaranteed_item_hint
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.db.dock_node import DockNode
from randovania.games.am2r.exporter.hint_namer import AM2RHintNamer
from randovania.games.am2r.exporter.joke_hints import AM2R_JOKE_HINTS
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.games.am2r.layout.am2r_cosmetic_patches import AM2RCosmeticPatches, MusicMode
from randovania.generator.pickup_pool import pickup_creator
from randovania.layout.base.hint_configuration import SpecificPickupHintMode
from randovania.layout.lib.teleporters import TeleporterShuffleMode
from randovania.lib import json_lib, random_lib

if TYPE_CHECKING:
    from randovania.exporter.pickup_exporter import ExportedPickupDetails
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry


def _construct_music_shuffle_dict(music_mode: MusicMode, rng: Random) -> dict[str, str]:
    combat_list = [
        "musalphafight",
        "musancientguardian",
        "musarachnus",
        "museris",
        "musgammafight",
        "musgenesis",
        "musomegafight",
        "musqueen",
        "musqueen2",
        "musqueen3",
        "musreactor",
        "mustorizoa",
        "mustorizob",
        "muszetafight",
        "mustester",
    ]

    exploration_list = [
        "musarea1a",
        "musarea1b",
        "musarea2a",
        "musarea2b",
        "musarea3a",
        "musarea3b",
        "musarea4a",
        "musarea4b",
        "musarea5a",
        "musarea5b",
        "musarea6a",
        "musarea7a",
        "musarea7c",
        "musarea8",
        "muscaveambience",
        "muscaveambiencea4",
        "mushatchling",
        "musitemamb",
        "musitemamb2",
        "muslabambience",
        "musmaincave",
        "musmaincave2",
        "mustitle",
    ]

    fanfare_list = [
        "musarea7b",
        "musfanfare",
        "musitemget",
        "musmonsterappear",
        "musqueenbreak",
        "musqueenintro",
    ]

    excluded_list = [
        "musarea7d",
        "muscredits",
        "musending",
        "musintroseq",
    ]

    if music_mode == MusicMode.VANILLA:
        return {}

    # Music is now either TYPE or FULL
    assert music_mode in (MusicMode.TYPE, MusicMode.FULL)

    total_orig = combat_list + exploration_list + fanfare_list

    if music_mode == MusicMode.FULL:
        total_orig += excluded_list
        total_new = random_lib.shuffle(rng, iter(total_orig))
    else:
        # MusicMode is TYPE
        shuffled_combat = random_lib.shuffle(rng, iter(combat_list))
        shuffled_exploration = random_lib.shuffle(rng, iter(exploration_list))
        shuffled_fanfare = random_lib.shuffle(rng, iter(fanfare_list))
        total_new = shuffled_combat + shuffled_exploration + shuffled_fanfare

    return {f"{orig}.ogg": f"{new}.ogg" for orig, new in zip(total_orig, total_new, strict=True)}


class AM2RPatchDataFactory(PatchDataFactory[AM2RConfiguration, AM2RCosmeticPatches]):
    _EASTER_EGG_SHINY = 1024

    # Effect, sprite, header => new_sprite, new_header
    SHINIES = {
        ("Missile Tank", "sItemMissile", "Got Missile Tank"): ("sItemShinyMissile", "Got Shiny Missile Tank"),
        ("Hi-Jump Boots", "sItemHijump", "Hi-Jump Boots acquired"): (
            "sItemShinyHijump",
            "Shiny Air Jordan Boots acquired",
        ),
        ("Screw Attack", "sItemScrewAttack", "Screw Attack acquired"): (
            "sItemShinyScrewAttack",
            "Shiny Screw Attacker acquired",
        ),
        ("Ice Beam", "sItemIceBeam", "Ice Beam acquired"): ("sItemShinyIceBeam", "Shiny Ice Cream acquired"),
        ("Nothing", "sItemNothing", "Nothing acquired"): ("sItemShinyNothing", "Shiny Nothing acquired"),
    }

    def _create_pickups_dict(
        self, pickup_list: list[ExportedPickupDetails], text_data: dict, model_data: dict[str, int], rng: Random
    ) -> dict:
        pickup_map_dict = {}
        for pickup in pickup_list:
            if not pickup.is_for_remote_player and pickup.conditional_resources[0].resources:
                quantity = pickup.conditional_resources[0].resources[0][1]
            else:
                quantity = 0
            object_name = self.game.region_list.node_from_pickup_index(pickup.index).extra["object_name"]
            res_lock = pickup.original_pickup.resource_lock
            text_index = (
                1
                if (
                    res_lock is not None
                    and "Locked" in res_lock.temporary_item.long_name
                    and len(pickup.collection_text) > 1
                )
                else 0
            )

            pickup_map_dict[object_name] = {
                "sprite_details": {
                    "name": pickup.model.name,
                    "speed": model_data.get(pickup.model.name, 0.2),
                },
                "item_effect": pickup.original_pickup.name if not pickup.is_for_remote_player else "Nothing",
                "quantity": quantity,
                "text": {
                    "header": (
                        text_data[pickup.name]["text_header"] if not self.players_config.is_multiworld else pickup.name
                    ),
                    "description": pickup.collection_text[text_index],
                },
            }

            pickup_obj = pickup_map_dict[object_name]
            shiny_id = (pickup_obj["item_effect"], pickup_obj["sprite_details"]["name"], pickup_obj["text"]["header"])

            if (
                (shiny_id in self.SHINIES)
                and not pickup.is_for_remote_player
                and rng.randint(0, self._EASTER_EGG_SHINY) == 0
            ):
                monitoring.metrics.incr("am2r_rolled_shiny", tags={"item": shiny_id[0]})
                sprite, text = self.SHINIES[shiny_id]
                pickup_obj["sprite_details"]["name"] = sprite
                pickup_obj["text"]["header"] = text

        return pickup_map_dict

    def _create_room_dict(self) -> dict:
        rng = Random(self.description.get_seed_for_world(self.players_config.player_index))

        return_dict = {}
        for region in self.game.region_list.regions:
            for area in region.areas:
                light_level = area.extra["light_level"]
                if rng.random() < (self.configuration.darkness_chance / 1000.0):
                    light_level = str(rng.randint(self.configuration.darkness_min, self.configuration.darkness_max))

                liquid_info = None
                # 0 - water, 1 - lava
                liquid_type = rng.choices(
                    [0, 1, None],
                    weights=[
                        self.configuration.submerged_water_chance,
                        self.configuration.submerged_lava_chance,
                        1000 - self.configuration.submerged_water_chance - self.configuration.submerged_lava_chance,
                    ],
                )[0]
                if liquid_type is not None:
                    liquid_info = {
                        "liquid_type": liquid_type,
                        "liquid_level": -100,
                        "should_be_at_very_front": True,
                    }
                else:
                    linfo = area.extra.get("liquid_info", {})
                    if len(linfo) > 0:
                        liquid_info = {
                            "liquid_type": linfo["liquid_type"],
                            "liquid_level": linfo["liquid_level"],
                            "should_move_horizontally": linfo.get("should_move_horizontally", False),
                            "should_wave": linfo.get("should_wave", False),
                            "wave_speed": linfo.get("wave_speed", 0),
                            "wave_height": linfo.get("wave_height", 0),
                            "should_be_at_very_front": linfo.get("should_be_at_very_front", False),
                        }

                return_dict[area.extra["map_name"]] = {
                    "display_name": area.name,
                    "region_name": region.name,
                    "minimap_data": area.extra["minimap_data"],
                    "light_level": light_level,
                    "liquid_info": liquid_info,
                }

        return return_dict

    def _create_starting_popup(self, patches: GamePatches) -> dict | None:
        extra_items = item_names.additional_starting_equipment(patches.configuration, patches.game, patches)
        if extra_items:
            i = 0
            items_with_length = [""]
            # Go through the items, so that we can wrap them
            for item in extra_items:
                if len(items_with_length[i] + item) < 60:
                    if items_with_length[i] != "":
                        items_with_length[i] = items_with_length[i] + ", " + item
                    else:
                        items_with_length[i] = item
                else:
                    i += 1
                    items_with_length.append(item)
            return {
                "header": "Extra starting items:",
                "description": "#".join(items_with_length),  # A '#' is a newline character in GameMaker
            }
        else:
            return None

    def _create_starting_items_dict(self) -> dict:
        starting_resources = self.patches.starting_resources()
        return {resource.long_name: quantity for resource, quantity in starting_resources.as_resource_gain()}

    def _create_starting_location(self) -> dict:
        return {
            "save_room": self.game.region_list.node_by_identifier(self.patches.starting_location).extra["save_room"]
        }

    def _create_hash_dict(self) -> dict:
        return_dict: dict = {
            "contains_spoiler": self.description.has_spoiler,
            "word_hash": self.description.shareable_word_hash,
            "hash": self.description.shareable_hash,
            "session_uuid": str(self.players_config.get_own_uuid()),
            "starting_memo": self._create_starting_popup(self.patches),
        }
        return return_dict

    def _create_game_patches(
        self, config: AM2RConfiguration, pickup_list: list[ExportedPickupDetails], text_data: dict, rng: Random
    ) -> dict:
        def get_locked_ammo_text(ammo_item: str) -> str:
            text = "MISSING TEXT, PLEASE REPORT THIS!"
            for pickup in pickup_list:
                if pickup.original_pickup.name != ammo_item:
                    continue
                text = pickup.collection_text[0]
                break
            return text

        missile_text = get_locked_ammo_text("Missile Tank")
        super_text = get_locked_ammo_text("Super Missile Tank")
        pb_text = get_locked_ammo_text("Power Bomb Tank")

        game_patches = {
            "septogg_helpers": config.septogg_helpers,
            "respawn_bomb_blocks": config.respawn_bomb_blocks,
            "skip_cutscenes": config.skip_cutscenes,
            "skip_save_cutscene": config.skip_save_cutscene,
            "skip_item_cutscenes": config.skip_item_cutscenes,
            "energy_per_tank": config.energy_per_tank,
            "one_suit_damage_multiplier": (1 - config.first_suit_dr / 100),
            "two_suits_damage_multiplier": (1 - config.second_suit_dr / 100),
            "grave_grotto_blocks": config.grave_grotto_blocks,
            "fusion_mode": config.fusion_mode,
            "supers_on_missile_doors": config.supers_on_missile_doors,
            "nest_pipes": config.nest_pipes,
            "softlock_prevention_blocks": config.softlock_prevention_blocks,
            "a3_entrance_blocks": config.a3_entrance_blocks,
            "screw_blocks": config.screw_blocks,
            "sabre_designed_skippy": rng.randint(0, self._EASTER_EGG_SHINY) == 0,
            "locked_missile_text": {
                "header": text_data["Locked Missile Tank"]["text_header"],
                "description": missile_text,
            },
            "locked_super_text": {
                "header": text_data["Locked Super Missile Tank"]["text_header"],
                "description": super_text,
            },
            "locked_pb_text": {
                "header": text_data["Locked Power Bomb Tank"]["text_header"],
                "description": pb_text,
            },
            "required_amount_of_dna": 46 - (config.artifacts.placed_artifacts - config.artifacts.required_artifacts),
            "flip_vertically": config.vertically_flip_gameplay,
            "flip_horizontally": config.horizontally_flip_gameplay,
        }
        for item, state in config.ammo_pickup_configuration.pickups_state.items():
            launcher_dict = {
                "Missile Tank": "require_missile_launcher",
                "Super Missile Tank": "require_super_launcher",
                "Power Bomb Tank": "require_pb_launcher",
            }
            key = launcher_dict.get(item.name)

            if key is None:
                continue

            game_patches[key] = state.requires_main_item
        return game_patches

    def _create_door_locks(self) -> dict:
        return {
            str(
                node.extra["door_instance_id"]
                if node.default_dock_weakness.name != "Open Transition"
                else node.extra["instance_id"]
            ): {
                "lock": weakness.extra.get("door_name", weakness.long_name),
                "is_dock": True if node.default_dock_weakness.extra.get("is_dock", None) is not None else False,
                "facing_direction": node.extra["facing"] if node.extra.get("facing", None) is not None else "invalid",
            }
            for node, weakness in self.patches.all_dock_weaknesses()
        }

    def _create_hints(self, rng: Random) -> dict:
        artifacts = [self.game.resource_database.get_item(f"Metroid DNA {i + 1}") for i in range(46)]
        ice = [(self.game.resource_database.get_item("Ice Beam"))]
        dna_hint_mapping = {}
        hint_config = self.configuration.hints
        hint_namer = AM2RHintNamer(self.description.all_patches, self.players_config)
        if hint_config.specific_pickup_hints["artifacts"] != SpecificPickupHintMode.DISABLED:
            dna_hint_mapping = guaranteed_item_hint.create_guaranteed_hints_for_resources(
                self.description.all_patches,
                self.players_config,
                hint_namer,
                hint_config.specific_pickup_hints["artifacts"] == SpecificPickupHintMode.HIDE_AREA,
                artifacts,
                True,
            )
        else:
            dna_hint_mapping = {k: f"{k.long_name} is hidden somewhere on SR-388." for k in artifacts}

        # Shuffle DNA hints
        hint_texts = list(dna_hint_mapping.values())
        rng.shuffle(hint_texts)
        dna_hint_mapping = dict(zip(artifacts, hint_texts))

        septogg_hints = {}
        gm_newline = "#-#"
        dud_hints = ["This creature did not give any useful DNA hints.", "Metroid DNA is hidden somewhere on SR-388."]
        joke_hints = AM2R_JOKE_HINTS + dud_hints
        area_to_amount_map = {0: (0, 5), 1: (5, 9), 2: (9, 17), 3: (17, 27), 4: (27, 33), 5: (33, 41), 6: (41, 46)}

        def _sort_list_by_region(entry: str) -> int:
            is_located_str = "is located in "
            index = entry.find("}", entry.find(is_located_str)) + 1
            for region in self.game.region_list.regions:
                if entry.startswith(region.name, index):
                    return region.extra["internal_number"]
            return 0

        for i in range(7):
            start, end = area_to_amount_map[i]
            shuffled_hints = list(dna_hint_mapping.values())[start:end]
            shuffled_hints = [
                hint
                for hint in shuffled_hints
                if not ("Hunter already started with" in hint or "is hidden somewhere on SR-388" in hint)
            ]
            if not shuffled_hints:
                joke = rng.choice(joke_hints)
                joke_hints.remove(joke)
                shuffled_hints = [hint_namer.format_joke(joke, True)]
            septogg_hints[f"septogg_a{i}"] = gm_newline.join(sorted(shuffled_hints, key=_sort_list_by_region))

        ice_hint = {}
        if hint_config.specific_pickup_hints["ice_beam"] != SpecificPickupHintMode.DISABLED:
            temp_ice_hint = guaranteed_item_hint.create_guaranteed_hints_for_resources(
                self.description.all_patches,
                self.players_config,
                hint_namer,
                hint_config.specific_pickup_hints["ice_beam"] == SpecificPickupHintMode.HIDE_AREA,
                ice,
                True,
            )
            ice_hint = {"chozo_labs": temp_ice_hint[ice[0]]}
        else:
            ice_hint = {
                "chozo_labs": "To combat our creations, we have created the Ice Beam. Unfortunately, "
                "we seem to have misplaced it."
            }

        hints = septogg_hints | ice_hint

        return hints

    def _create_cosmetics(self, seed_number: int) -> dict:
        c = self.cosmetic_patches
        return {
            "show_unexplored_map": c.show_unexplored_map,
            "unveiled_blocks": c.unveiled_blocks,
            "health_hud_rotation": c.health_hud_rotation,
            "etank_hud_rotation": c.etank_hud_rotation,
            "dna_hud_rotation": c.dna_hud_rotation,
            "tileset_rotation": Random(seed_number).randint(c.tileset_rotation_min, c.tileset_rotation_max),
            "background_rotation": Random(seed_number).randint(c.background_rotation_min, c.background_rotation_max),
            "room_names_on_hud": c.show_room_names.value,
            "music_shuffle": _construct_music_shuffle_dict(c.music, Random(seed_number)),
        }

    def _get_text_data(self) -> dict:
        text_data: dict = typing.cast(
            "dict", json_lib.read_path(RandovaniaGame.AM2R.data_path.joinpath("pickup_database", "text_data.json"))
        )

        for i in range(1, 47):
            text_data[f"Metroid DNA {i}"] = text_data["Metroid DNA"]

        text_data["Missiles"] = text_data["Missile Tank"]
        text_data["Super Missiles"] = text_data["Super Missile Tank"]
        text_data["Power Bombs"] = text_data["Power Bomb Tank"]
        text_data["EnergyTransferModule"] = text_data["Nothing"]
        return text_data

    def _get_model_data(self) -> dict[str, int]:
        return typing.cast(
            "dict[str, int]",
            json_lib.read_path(RandovaniaGame.AM2R.data_path.joinpath("pickup_database", "model_data.json")),
        )

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.AM2R

    @override
    @classmethod
    def hint_namer_type(cls) -> type[AM2RHintNamer]:
        return AM2RHintNamer

    def _credits_spoiler(self) -> str:
        spoiler = "*Major Item Locations;;"
        spoiler_dict = credits_spoiler.generic_credits(
            self.configuration.standard_pickup_configuration,
            self.description.all_patches,
            self.players_config,
            AM2RHintNamer(self.description.all_patches, self.players_config),
            "{}",
            False,
        )
        # am2r credits uses the following syntax:
        # * indicates a header
        # ; indicates a newline
        # / indicates centered text
        # = splits into left/right adjusted text, but its irrelevant here.
        for key, value in spoiler_dict.items():
            if "\n" in value:
                value = value.replace("\n", ";/")
            spoiler += f"*{key};/{value};;"

        if not spoiler:
            spoiler += ";;"

        return spoiler

    def create_memo_data(self) -> dict:
        """Used to generate pickup collection messages."""
        text_data = self._get_text_data()
        memo_data = {key: value["text_desc"] for key, value in text_data.items()}
        memo_data["Energy Tank"] = memo_data["Energy Tank"].format(Energy=self.configuration.energy_per_tank)
        return memo_data

    def create_useless_pickup(self) -> PickupEntry:
        """Used for any location with no PickupEntry assigned to it."""
        return pickup_creator.create_nothing_pickup(
            self.game.resource_database,
            model_name="sItemNothing",
        )

    def create_visual_nothing(self) -> PickupEntry:
        """The model of this pickup replaces the model of all pickups when PickupModelDataSource is ETM"""
        return pickup_creator.create_visual_nothing(self.game_enum(), "sItemUnknown")

    def create_game_specific_data(self) -> dict:
        text_data = self._get_text_data()
        model_data = self._get_model_data()

        pickup_list = self.export_pickup_list()

        pipes = {
            str(node.extra["instance_id"]): {
                "dest_x": connection.extra["dest_x"],
                "dest_y": connection.extra["dest_y"],
                "dest_room": self.game.region_list.area_by_area_location(connection.identifier.area_identifier).extra[
                    "map_name"
                ],
            }
            for node, connection in self.patches.all_dock_connections()
            if (
                isinstance(node, DockNode)
                and node.dock_type in self.game.dock_weakness_database.all_teleporter_dock_types
            )
        }

        return {
            "configuration_identifier": self._create_hash_dict(),
            "starting_items": self._create_starting_items_dict(),
            "starting_location": self._create_starting_location(),
            "pickups": self._create_pickups_dict(pickup_list, text_data, model_data, self.rng),
            "rooms": self._create_room_dict(),
            "game_patches": self._create_game_patches(self.configuration, pickup_list, text_data, self.rng),
            "pipes": pipes if self.configuration.teleporters.mode != TeleporterShuffleMode.VANILLA else {},
            "door_locks": self._create_door_locks(),
            "hints": self._create_hints(self.rng),
            "cosmetics": self._create_cosmetics(self.description.get_seed_for_world(self.players_config.player_index)),
            "credits_spoiler": self._credits_spoiler(),
        }
