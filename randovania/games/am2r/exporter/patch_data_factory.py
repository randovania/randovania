from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter import pickup_exporter
from randovania.exporter.hints import guaranteed_item_hint
from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.game_description.assignment import PickupTarget
from randovania.games.am2r.exporter.hint_namer import AM2RHintNamer
from randovania.games.am2r.layout.hint_configuration import ItemHintMode
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pickup_creator
from randovania.lib import json_lib

if TYPE_CHECKING:
    from random import Random

    from randovania.exporter.pickup_exporter import ExportedPickupDetails


class AM2RPatchDataFactory(BasePatchDataFactory):
    _EASTER_EGG_SHINY = 1024

    # Effect, sprite, header => new_sprite, new_header
    SHINIES = {
        ("Missile Expansion", "sItemMissile", "Got Missile Tank"): (
            "sItemShinyMissile", "Got Shiny Missile Tank"),
        ("Hi-Jump Boots", "sItemHijump", "Hi-Jump Boots acquired"): (
            "sItemShinyHijump", "Shiny Air Jordan Boots acquired"),
        ("Screw Attack", "sItemScrewAttack", "Screw Attack acquired"): (
            "sItemShinyScrewAttack", "Shiny Screw Attacker acquired"),
        ("Ice Beam", "sItemIceBeam", "Ice Beam acquired"): ("sItemShinyIceBeam", "Shiny Ice Cream acquired"),
        ("Nothing", "sItemNothing", "Nothing acquired"): ("sItemShinyNothing", "Shiny Nothing acquired"),
    }

    def _create_pickups_dict(self, pickup_list: list[ExportedPickupDetails], item_info: dict, rng: Random):
        pickup_map_dict = {}
        for pickup in pickup_list:
            quantity = pickup.conditional_resources[0].resources[0][1]
            object_name = self.game.region_list.node_from_pickup_index(pickup.index).extra["object_name"]
            pickup_map_dict[object_name] = {
                "sprite_details": {
                    "name": pickup.model.name,
                    "speed": item_info[pickup.original_pickup.name]["sprite_speed"]
                },
                "item_effect": pickup.original_pickup.name,
                "quantity": quantity,
                "text": {
                    "header": item_info[pickup.name]["text_header"],
                    "description": pickup.collection_text[0]
                }
            }

            pickup_obj = pickup_map_dict[object_name]
            shiny_id = (pickup_obj["item_effect"], pickup_obj["sprite_details"]["name"], pickup_obj["text"]["header"])

            if (shiny_id in self.SHINIES) and not pickup.other_player and rng.randint(0, self._EASTER_EGG_SHINY) == 0:
                sprite, text = self.SHINIES[shiny_id]
                pickup_obj["sprite_details"]["name"] = sprite
                pickup_obj["text"]["header"] = text

        return pickup_map_dict

    def _create_room_dict(self):
        return {
            area.extra["map_name"]: {"display_name": area.name}
            for area in self.game.region_list.all_areas
        }

    def _create_starting_items_dict(self):
        starting_resources = self.patches.starting_resources()
        return {
            resource.short_name: quantity
            for resource, quantity in starting_resources.as_resource_gain()
        }

    def _create_starting_location(self):
        return {
            "save_room": self.game.region_list.node_by_identifier(self.patches.starting_location).extra["save_room"]
        }

    def _create_hash_dict(self):
        return {
            "word_hash": self.description.shareable_word_hash,
            "hash": self.description.shareable_hash,
            "session_uuid": str(self.players_config.get_own_uuid())
        }

    def _create_game_patches(self):
        game_patches = {
            "septogg_helpers": self.patches.configuration.septogg_helpers,
            "respawn_bomb_blocks": self.patches.configuration.respawn_bomb_blocks,
            "skip_cutscenes": self.patches.configuration.skip_cutscenes,
            "energy_per_tank": self.patches.configuration.energy_per_tank,
            "grave_grotto_blocks": self.patches.configuration.grave_grotto_blocks,
            "fusion_mode": self.patches.configuration.fusion_mode,
            "nest_pipes": self.patches.configuration.nest_pipes,
            "softlock_prevention_blocks": self.patches.configuration.softlock_prevention_blocks,
            "a3_entrance_blocks": self.patches.configuration.a3_entrance_blocks,
            "screw_blocks": self.patches.configuration.screw_blocks,
        }
        for item, state in self.patches.configuration.ammo_pickup_configuration.pickups_state.items():
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

    def _create_door_locks(self):
        return {
            str(node.extra["instance_id"]): {
                "lock": weakness.long_name
            }
            for node, weakness in self.patches.all_dock_weaknesses()
        }

    def _create_hints(self):
        artifacts = [self.game.resource_database.get_item(f"Metroid DNA {i + 1}") for i in range(46)]
        ice = [(self.game.resource_database.get_item("Ice Beam"))]
        artifact_hints = {}
        hint_config = self.patches.configuration.hints
        if hint_config.artifacts != ItemHintMode.DISABLED:
            artifact_hints = guaranteed_item_hint.create_guaranteed_hints_for_resources(
                self.description.all_patches,
                self.players_config,
                AM2RHintNamer(self.description.all_patches, self.players_config),
                hint_config.artifacts == ItemHintMode.HIDE_AREA,
                artifacts,
                False  # TODO: set this to true, when patcher supports setting colors!
            )
        else:
            artifact_hints = {k: f"{k.long_name} is hidden somewhere on SR-388." for k in artifacts}

        ice_hint = {}
        if hint_config.ice_beam != ItemHintMode.DISABLED:
            ice_hint = guaranteed_item_hint.create_guaranteed_hints_for_resources(
                self.description.all_patches,
                self.players_config,
                AM2RHintNamer(self.description.all_patches, self.players_config),
                hint_config.ice_beam == ItemHintMode.HIDE_AREA,
                ice,
                False  # TODO: set this to true, when patcher supports setting colors!
            )
        else:
            ice_hint = {
                k: "To combat our creations, we have created the Ice Beam. Unfortunately, we seem to have misplaced it."
                for k in ice}

        hints = artifact_hints | ice_hint

        return {
            key.long_name: value
            for key, value in hints.items()
        }

    def _create_cosmetics(self):
        c = self.cosmetic_patches
        return {
            "show_unexplored_map": c.show_unexplored_map,
            "unveiled_blocks": c.unveiled_blocks,
            "health_hud_rotation": c.health_hud_rotation,
            "etank_hud_rotation": c.etank_hud_rotation,
            "dna_hud_rotation": c.dna_hud_rotation
        }

    def _get_item_data(self):
        item_data = json_lib.read_path(
            RandovaniaGame.AM2R.data_path.joinpath("pickup_database", "item_data.json")
        )

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

        useless_target = PickupTarget(pickup_creator.create_nothing_pickup(db.resource_database, "sItemNothing"),
                                      self.players_config.player_index)

        item_data = self._get_item_data()
        memo_data = {
            key: value["text_desc"]
            for key, value in item_data.items()
        }
        memo_data["Energy Tank"] = memo_data["Energy Tank"].format(Energy=self.patches.configuration.energy_per_tank)

        pickup_list = pickup_exporter.export_all_indices(
            self.patches,
            useless_target,
            self.game.region_list,
            self.rng,
            self.configuration.pickup_model_style,
            self.configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(memo_data, self.players_config, self.game),
            visual_etm=pickup_creator.create_visual_etm(),
        )

        return {
            "configuration_identifier": self._create_hash_dict(),
            "starting_items": self._create_starting_items_dict(),
            "starting_location": self._create_starting_location(),
            "pickups": self._create_pickups_dict(pickup_list, item_data, self.rng),
            "rooms": self._create_room_dict(),
            "game_patches": self._create_game_patches(),
            "door_locks": self._create_door_locks(),
            "hints": self._create_hints(),
            "cosmetics": self._create_cosmetics()
        }
