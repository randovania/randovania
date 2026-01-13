from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, override

from randovania.exporter import item_names
from randovania.exporter.hints import credits_spoiler
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.games.planets_zebeth.exporter.hint_namer import PlanetsZebethHintNamer
from randovania.games.planets_zebeth.layout.planets_zebeth_configuration import PlanetsZebethConfiguration
from randovania.games.planets_zebeth.layout.planets_zebeth_cosmetic_patches import PlanetsZebethCosmeticPatches
from randovania.generator.pickup_pool import pickup_creator
from randovania.lib import json_lib

if TYPE_CHECKING:
    from random import Random

    from randovania.exporter.patch_data_factory import PatcherDataMeta
    from randovania.exporter.pickup_exporter import ExportedPickupDetails
    from randovania.game_description.pickup.pickup_entry import PickupEntry


MAX_CHARS_LIMIT_FOR_INGAME_MESSAGE_BOX = 33


class PlanetsZebethPatchDataFactory(PatchDataFactory[PlanetsZebethConfiguration, PlanetsZebethCosmeticPatches]):
    @override
    @classmethod
    def hint_namer_type(cls) -> type[PlanetsZebethHintNamer]:
        return PlanetsZebethHintNamer

    def _create_pickups_dict(self, pickup_list: list[ExportedPickupDetails], _rng: Random) -> dict:
        def get_locked_ammo_text(ammo_item: str) -> str:
            text = "MISSING TEXT, PLEASE REPORT THIS!"
            for pickup in pickup_list:
                if pickup.original_pickup.name != ammo_item:
                    continue
                text = pickup.collection_text[0]
                break
            return text

        pickup_map_dict = {}
        for pickup in pickup_list:
            quantity = pickup.conditional_resources[0].resources[0][1] if not pickup.is_for_remote_player else 0
            object_id = str(self.game.region_list.node_from_pickup_index(pickup.index).extra["object_id"])
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

            pickup_type = "Nothing"
            if not pickup.is_for_remote_player:
                if pickup.original_pickup.name.startswith("Tourian Key"):
                    pickup_type = "Tourian Key"
                else:
                    pickup_type = pickup.original_pickup.name

            acquired_msg = pickup.name
            if not self.players_config.is_multiworld:
                acquired_msg = f"{pickup.original_pickup.name} acquired"

            pickup_map_dict[object_id] = {
                "model": pickup.model.name,
                "type": pickup_type,
                "quantity": quantity,
                "text": {
                    "header": acquired_msg,
                    "description": textwrap.wrap(
                        pickup.collection_text[text_index], width=MAX_CHARS_LIMIT_FOR_INGAME_MESSAGE_BOX
                    ),
                },
            }

            if pickup.name == "Missile Launcher":
                pickup_map_dict[object_id].update(
                    {
                        "is_launcher": True,
                    }
                )

            # aka Big Missile Tank and Missile Tank
            if pickup.name.endswith("Missile Tank"):
                pickup_map_dict[object_id].update(
                    {
                        "locked_text": {
                            "header": f"Locked {acquired_msg}",
                            "description": textwrap.wrap(
                                get_locked_ammo_text(pickup.name),
                                width=MAX_CHARS_LIMIT_FOR_INGAME_MESSAGE_BOX,
                            ),
                        }
                    }
                )

        return pickup_map_dict

    def _create_starting_items_dict(self) -> dict:
        starting_resources = self.patches.starting_resources()
        return {resource.long_name: quantity for resource, quantity in starting_resources.as_resource_gain()}

    def _create_starting_memo(self) -> dict:
        starting_memo = None
        extra_starting = item_names.additional_starting_equipment(self.configuration, self.game, self.patches)
        if extra_starting:
            starting_memo = ", ".join(extra_starting)

        if starting_memo is not None:
            return {
                "header": "Extra Starting Items",
                "description": textwrap.wrap(starting_memo, width=MAX_CHARS_LIMIT_FOR_INGAME_MESSAGE_BOX),
            }

    def _create_starting_location(self) -> dict:
        return {
            "x": self.game.region_list.node_by_identifier(self.patches.starting_location).extra["global_x"],
            "y": self.game.region_list.node_by_identifier(self.patches.starting_location).extra["global_y"],
        }

    def _create_hash_dict(self) -> dict:
        return {
            "word_hash": self.description.shareable_word_hash,
            "hash": self.description.shareable_hash,
            "session_uuid": str(self.players_config.get_own_uuid()),
        }

    def _create_game_config_dict(self):
        return {
            "starting_room": self._create_starting_location(),
            "seed_identifier": self._create_hash_dict(),
            "starting_items": self._create_starting_items_dict(),
            "starting_memo": self._create_starting_memo(),
            "warp_to_start": self.configuration.warp_to_start,
            "open_missile_doors_with_one_missile": self.configuration.open_missile_doors_with_one_missile,
            "allow_downward_shots": self.configuration.allow_downward_shots,
            "credits_string": self._credits_spoiler(),
        }

    def _create_cosmetics(self) -> dict:
        c = self.cosmetic_patches
        return {
            "disable_low_health_beeping": c.disable_low_health_beeping,
            "room_names_on_hud": c.show_room_names.value,
            "show_unexplored_map": c.show_unexplored_map,
            "use_alternative_escape_theme": c.use_alternative_escape_theme,
            "use_sm_boss_theme": c.use_sm_boss_theme,
        }

    def _get_item_data(self) -> dict:
        item_data: dict = json_lib.read_path(
            RandovaniaGame.METROID_PLANETS_ZEBETH.data_path.joinpath("pickup_database", "item_data.json")
        )

        for i in range(1, 10):
            item_data[f"Tourian Key {i}"] = item_data["Tourian Key"]
        item_data["Missiles"] = item_data["Missile Tank"]
        item_data["EnergyTransferModule"] = item_data["Nothing"]
        return item_data

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_PLANETS_ZEBETH

    def _credits_spoiler(self) -> list:
        spoiler = []
        spoiler_dict = credits_spoiler.generic_string_credits(
            self.configuration.standard_pickup_configuration,
            self.description.all_patches,
            self.players_config,
            PlanetsZebethHintNamer(self.description.all_patches, self.players_config),
            "{}",
            False,
        )
        for key, value in spoiler_dict.items():
            spoiler.append(
                {
                    "header": key,
                    "description": value.split("\n"),
                }
            )

        return spoiler

    def create_memo_data(self) -> dict:
        """Used to generate pickup collection messages."""
        memo_data = self._get_item_data()
        memo_data["Energy Tank"] = memo_data["Energy Tank"].format(Energy=self.configuration.energy_per_tank)
        return memo_data

    def create_useless_pickup(self) -> PickupEntry:
        """Used for any location with no PickupEntry assigned to it."""
        return pickup_creator.create_nothing_pickup(
            self.game.get_resource_database_view(),
            model_name="spr_ITEM_Nothing",
        )

    def create_visual_nothing(self) -> PickupEntry:
        """The model of this pickup replaces the model of all pickups when PickupModelDataSource is ETM"""
        return pickup_creator.create_visual_nothing(self.game_enum(), "spr_ITEM_Nothing")

    def create_game_specific_data(self, randovania_meta: PatcherDataMeta) -> dict:
        pickup_list = self.export_pickup_list()

        return {
            "seed": self.description.get_seed_for_world(self.players_config.player_index),
            "game_config": self._create_game_config_dict(),
            "preferences": self._create_cosmetics(),
            "level_data": {"room": "rm_Zebeth", "pickups": self._create_pickups_dict(pickup_list, self.rng)},
        }
