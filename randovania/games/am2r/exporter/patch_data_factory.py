from __future__ import annotations

from random import Random
from typing import TYPE_CHECKING

from randovania.exporter import pickup_exporter
from randovania.exporter.hints import guaranteed_item_hint
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game_description.assignment import PickupTarget
from randovania.games.am2r.exporter.hint_namer import AM2RHintNamer
from randovania.games.am2r.exporter.joke_hints import JOKE_HINTS
from randovania.games.am2r.layout.am2r_cosmetic_patches import AM2RCosmeticPatches, MusicMode
from randovania.games.am2r.layout.hint_configuration import ItemHintMode
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pickup_creator
from randovania.lib import json_lib, random_lib

if TYPE_CHECKING:
    from randovania.exporter.pickup_exporter import ExportedPickupDetails
    from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration


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
        total_new = random_lib.shuffle(rng, total_orig)
    else:
        # MusicMode is TYPE
        # TODO: copying is not necessary anymore, clean this up in the future.
        shuffled_combat = combat_list.copy()
        shuffled_exploration = exploration_list.copy()
        shuffled_fanfare = fanfare_list.copy()
        rng.shuffle(shuffled_combat)
        rng.shuffle(shuffled_exploration)
        rng.shuffle(shuffled_fanfare)
        total_new = shuffled_combat + shuffled_exploration + shuffled_fanfare

    return {f"{orig}.ogg": f"{new}.ogg" for orig, new in zip(total_orig, total_new, strict=True)}


class AM2RPatchDataFactory(PatchDataFactory):
    _EASTER_EGG_SHINY = 1024
    cosmetic_patches: AM2RCosmeticPatches
    configuration: AM2RConfiguration

    # Effect, sprite, header => new_sprite, new_header
    SHINIES = {
        ("Missile Expansion", "sItemMissile", "Got Missile Tank"): ("sItemShinyMissile", "Got Shiny Missile Tank"),
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

    def _create_pickups_dict(self, pickup_list: list[ExportedPickupDetails], item_info: dict, rng: Random) -> dict:
        pickup_map_dict = {}
        for pickup in pickup_list:
            quantity = pickup.conditional_resources[0].resources[0][1] if not pickup.other_player else 0
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
                    "speed": item_info[pickup.original_pickup.name]["sprite_speed"],
                },
                "item_effect": pickup.original_pickup.name if not pickup.other_player else "Nothing",
                "quantity": quantity,
                "text": {
                    "header": item_info[pickup.name]["text_header"]
                    if not self.players_config.is_multiworld
                    else pickup.name,
                    "description": pickup.collection_text[text_index],
                },
            }

            pickup_obj = pickup_map_dict[object_name]
            shiny_id = (pickup_obj["item_effect"], pickup_obj["sprite_details"]["name"], pickup_obj["text"]["header"])

            if (shiny_id in self.SHINIES) and not pickup.other_player and rng.randint(0, self._EASTER_EGG_SHINY) == 0:
                sprite, text = self.SHINIES[shiny_id]
                pickup_obj["sprite_details"]["name"] = sprite
                pickup_obj["text"]["header"] = text

        return pickup_map_dict

    def _create_room_dict(self) -> dict:
        return {
            area.extra["map_name"]: {
                "display_name": area.name,
                "region_name": region.name,
                "minimap_data": area.extra["minimap_data"],
            }
            for region in self.game.region_list.regions
            for area in region.areas
        }

    def _create_starting_items_dict(self) -> dict:
        starting_resources = self.patches.starting_resources()
        return {resource.long_name: quantity for resource, quantity in starting_resources.as_resource_gain()}

    def _create_starting_location(self) -> dict:
        return {
            "save_room": self.game.region_list.node_by_identifier(self.patches.starting_location).extra["save_room"]
        }

    def _create_hash_dict(self) -> dict:
        return {
            "word_hash": self.description.shareable_word_hash,
            "hash": self.description.shareable_hash,
            "session_uuid": str(self.players_config.get_own_uuid()),
        }

    def _create_game_patches(
        self, config: AM2RConfiguration, pickup_list: list[ExportedPickupDetails], item_info: dict, rng: Random
    ) -> dict:
        def get_locked_ammo_text(ammo_item: str) -> str:
            text = "MISSING TEXT, PLEASE REPORT THIS!"
            for pickup in pickup_list:
                if pickup.original_pickup.name != ammo_item:
                    continue
                text = pickup.collection_text[0]
                break
            return text

        missile_text = get_locked_ammo_text("Missile Expansion")
        super_text = get_locked_ammo_text("Super Missile Expansion")
        pb_text = get_locked_ammo_text("Power Bomb Expansion")

        game_patches = {
            "septogg_helpers": config.septogg_helpers,
            "respawn_bomb_blocks": config.respawn_bomb_blocks,
            "skip_cutscenes": config.skip_cutscenes,
            "skip_save_cutscene": config.skip_save_cutscene,
            "skip_item_cutscenes": config.skip_item_cutscenes,
            "energy_per_tank": config.energy_per_tank,
            "grave_grotto_blocks": config.grave_grotto_blocks,
            "fusion_mode": config.fusion_mode,
            "supers_on_missile_doors": config.supers_on_missile_doors,
            "nest_pipes": config.nest_pipes,
            "softlock_prevention_blocks": config.softlock_prevention_blocks,
            "a3_entrance_blocks": config.a3_entrance_blocks,
            "screw_blocks": config.screw_blocks,
            "sabre_designed_skippy": rng.randint(0, self._EASTER_EGG_SHINY) == 0,
            "locked_missile_text": {
                "header": item_info["Locked Missile Expansion"]["text_header"],
                "description": missile_text,
            },
            "locked_super_text": {
                "header": item_info["Locked Super Missile Expansion"]["text_header"],
                "description": super_text,
            },
            "locked_pb_text": {
                "header": item_info["Locked Power Bomb Expansion"]["text_header"],
                "description": pb_text,
            },
        }
        for item, state in config.ammo_pickup_configuration.pickups_state.items():
            launcher_dict = {
                "Missile Expansion": "require_missile_launcher",
                "Super Missile Expansion": "require_super_launcher",
                "Power Bomb Expansion": "require_pb_launcher",
            }
            key = launcher_dict.get(item.name)

            if key is None:
                continue

            game_patches[key] = state.requires_main_item
        return game_patches

    def _create_door_locks(self) -> dict:
        return {
            str(node.extra["instance_id"]): {"lock": weakness.long_name}
            for node, weakness in self.patches.all_dock_weaknesses()
        }

    def _create_hints(self, rng: Random) -> dict:
        artifacts = [self.game.resource_database.get_item(f"Metroid DNA {i + 1}") for i in range(46)]
        ice = [(self.game.resource_database.get_item("Ice Beam"))]
        dna_hint_mapping = {}
        hint_config = self.configuration.hints
        if hint_config.artifacts != ItemHintMode.DISABLED:
            dna_hint_mapping = guaranteed_item_hint.create_guaranteed_hints_for_resources(
                self.description.all_patches,
                self.players_config,
                AM2RHintNamer(self.description.all_patches, self.players_config),
                hint_config.artifacts == ItemHintMode.HIDE_AREA,
                artifacts,
                False,  # TODO: set this to true, when patcher supports setting colors!
            )
        else:
            dna_hint_mapping = {k: f"{k.long_name} is hidden somewhere on SR-388." for k in artifacts}

        # Shuffle DNA hints
        hint_texts = list(dna_hint_mapping.values())
        rng.shuffle(hint_texts)
        dna_hint_mapping = dict(zip(artifacts, hint_texts))

        septogg_hints = {}
        gm_newline = "#-#"
        dud_hint = "This creature did not give any useful DNA hints."
        area_to_amount_map = {0: (0, 5), 1: (5, 9), 2: (9, 17), 3: (17, 27), 4: (27, 33), 5: (33, 41), 6: (41, 46)}
        for i in range(7):
            start, end = area_to_amount_map[i]
            shuffled_hints = list(dna_hint_mapping.values())[start:end]
            shuffled_hints = [hint for hint in shuffled_hints if "Hunter already started with" not in hint]
            if not shuffled_hints:
                shuffled_hints = [rng.choice(JOKE_HINTS + [dud_hint])]
            septogg_hints[f"septogg_a{i}"] = gm_newline.join(shuffled_hints)

        ice_hint = {}
        if hint_config.ice_beam != ItemHintMode.DISABLED:
            temp_ice_hint = guaranteed_item_hint.create_guaranteed_hints_for_resources(
                self.description.all_patches,
                self.players_config,
                AM2RHintNamer(self.description.all_patches, self.players_config),
                hint_config.ice_beam == ItemHintMode.HIDE_AREA,
                ice,
                False,  # TODO: set this to true, when patcher supports setting colors!
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
            "room_names_on_hud": c.show_room_names.value,
            "music_shuffle": _construct_music_shuffle_dict(c.music, Random(seed_number)),
        }

    def _get_item_data(self):
        item_data = json_lib.read_path(RandovaniaGame.AM2R.data_path.joinpath("pickup_database", "item_data.json"))

        for i in range(1, 47):
            item_data[f"Metroid DNA {i}"] = item_data["Metroid DNA"]

        item_data["Missiles"] = item_data["Missile Expansion"]
        item_data["Super Missiles"] = item_data["Super Missile Expansion"]
        item_data["Power Bombs"] = item_data["Power Bomb Expansion"]
        item_data["EnergyTransferModule"] = item_data["Nothing"]
        return item_data

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.AM2R

    def create_data(self) -> dict:
        db = self.game

        useless_target = PickupTarget(
            pickup_creator.create_nothing_pickup(db.resource_database, "sItemNothing"), self.players_config.player_index
        )

        item_data = self._get_item_data()
        memo_data = {key: value["text_desc"] for key, value in item_data.items()}
        memo_data["Energy Tank"] = memo_data["Energy Tank"].format(Energy=self.configuration.energy_per_tank)

        pickup_list = pickup_exporter.export_all_indices(
            self.patches,
            useless_target,
            self.game.region_list,
            self.rng,
            self.configuration.pickup_model_style,
            self.configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(memo_data, self.players_config, self.game_enum()),
            visual_nothing=pickup_creator.create_visual_nothing(self.game_enum(), "sItemUnknown"),
        )

        return {
            "configuration_identifier": self._create_hash_dict(),
            "starting_items": self._create_starting_items_dict(),
            "starting_location": self._create_starting_location(),
            "pickups": self._create_pickups_dict(pickup_list, item_data, self.rng),
            "rooms": self._create_room_dict(),
            "game_patches": self._create_game_patches(self.configuration, pickup_list, item_data, self.rng),
            "door_locks": self._create_door_locks(),
            "hints": self._create_hints(self.rng),
            "cosmetics": self._create_cosmetics(self.description.get_seed_for_player(self.players_config.player_index)),
        }
