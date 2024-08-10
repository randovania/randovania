from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter import item_names, pickup_exporter
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game_description.assignment import PickupTarget
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pickup_creator
from randovania.lib import json_lib

if TYPE_CHECKING:
    from random import Random

    from randovania.exporter.pickup_exporter import ExportedPickupDetails
    from randovania.games.planets_zebeth.layout.planets_zebeth_configuration import PlanetsZebethConfiguration
    from randovania.games.planets_zebeth.layout.planets_zebeth_cosmetic_patches import PlanetsZebethCosmeticPatches


class PlanetsZebethPatchDataFactory(PatchDataFactory):
    cosmetic_patches: PlanetsZebethCosmeticPatches
    configuration: PlanetsZebethConfiguration

    def _create_pickups_dict(self, pickup_list: list[ExportedPickupDetails], item_info: dict, rng: Random) -> dict:
        pickup_map_dict = {}
        for pickup in pickup_list:
            quantity = pickup.conditional_resources[0].resources[0][1] if not pickup.other_player else 0
            object_id = self.game.region_list.node_from_pickup_index(pickup.index).extra["object_id"]
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

            pickup_map_dict[object_id] = {
                "model": pickup.model.name,
                "type": pickup.original_pickup.name if not pickup.other_player else "Nothing",
                "quantity": quantity,
                "text": {
                    "header": item_info[pickup.name]["text_header"]
                    if not self.players_config.is_multiworld
                    else pickup.name,
                    "description": pickup.collection_text[text_index],
                },
            }

        return pickup_map_dict

    def _create_starting_items_dict(self) -> dict:
        starting_resources = self.patches.starting_resources()
        return {resource.long_name: quantity for resource, quantity in starting_resources.as_resource_gain()}

    def _create_starting_memo(self) -> str:
        starting_memo = None
        extra_starting = item_names.additional_starting_equipment(self.configuration, self.game, self.patches)
        if extra_starting:
            starting_memo = ", ".join(extra_starting)
        return starting_memo

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
        }

    def _create_cosmetics(self) -> dict:
        c = self.cosmetic_patches
        return {
            "show_unexplored_map": c.show_unexplored_map,
            "room_names_on_hud": c.show_room_names.value,
        }

    def _get_item_data(self):
        item_data = json_lib.read_path(
            RandovaniaGame.METROID_PLANETS_ZEBETH.data_path.joinpath("pickup_database", "item_data.json")
        )

        item_data["Missiles"] = item_data["Missile Tank"]
        item_data["EnergyTransferModule"] = item_data["Nothing"]
        return item_data

    def _create_object_datas(self):
        pass

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_PLANETS_ZEBETH

    def create_data(self) -> dict:
        db = self.game

        useless_target = PickupTarget(
            pickup_creator.create_nothing_pickup(db.resource_database, "spr_ITEM_Nothing"),
            self.players_config.player_index,
        )

        item_data = self._get_item_data()
        memo_data = {key: value["text_desc"] for key, value in item_data.items()}
        memo_data["Energy Tank"] = memo_data["Energy Tank"].format(Energy=100)

        pickup_list = pickup_exporter.export_all_indices(
            self.patches,
            useless_target,
            self.game.region_list,
            self.rng,
            self.configuration.pickup_model_style,
            self.configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(memo_data, self.players_config, self.game_enum()),
            visual_nothing=pickup_creator.create_visual_nothing(self.game_enum(), "spr_ITEM_Nothing"),
        )

        return {
            "seed": self.description.get_seed_for_player(self.players_config.player_index),
            "game_config": self._create_game_config_dict(),
            "preferences": self._create_cosmetics(),
            "level_data": {"room": "rm_Zebeth", "pickups": self._create_pickups_dict(pickup_list, item_data, self.rng)},
        }
