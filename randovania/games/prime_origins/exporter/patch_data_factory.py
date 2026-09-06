from __future__ import annotations

import typing
from typing import TYPE_CHECKING, Any, override

import randovania
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime_origins.exporter.hint_namer import MPOHintNamer
from randovania.games.prime_origins.layout import MPOConfiguration, MPOCosmeticPatches
from randovania.generator.pickup_pool import pickup_creator
from randovania.lib import json_lib

if TYPE_CHECKING:
    from randovania.exporter.hints.hint_namer import HintNamer
    from randovania.exporter.patch_data_factory import PatcherDataMeta
    from randovania.exporter.pickup_exporter import ExportedPickupDetails
    from randovania.game_description.pickup.pickup_entry import PickupEntry


class MPOPatchDataFactory(PatchDataFactory[MPOConfiguration, MPOCosmeticPatches]):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.PRIME_ORIGINS

    def create_visual_nothing(self) -> PickupEntry:
        """The model of this pickup replaces the model of all pickups when PickupModelDataSource is ETM"""
        return pickup_creator.create_visual_nothing(self.game_enum(), "sItemUnknown")

    def _create_identifier(self) -> dict:
        return {
            "hash": self.description.shareable_hash,
            "word_hash": self.description.shareable_word_hash,
            "randovania_version": f"Randovania {randovania.VERSION}",
        }

    def _create_starting_items(self) -> dict:
        starting_resources = self.patches.starting_resources()
        starting_dict = {resource.long_name: quantity for resource, quantity in starting_resources.as_resource_gain()}
        res = {
            "energy_tanks": starting_dict.get("Energy Tank", 0),
            "missiles": starting_dict.get("Missile", 0),
            "power_bombs": starting_dict.get("Power Bomb", 0),
            "upgrades": list(starting_dict.keys()),
            "aeon": [],
        }

        return res

    def _create_starting_location(self) -> dict:
        node = self.game.region_list.node_by_identifier(self.patches.starting_location)
        _, area = self.game.region_list.region_and_area_by_area_identifier(self.patches.starting_location)

        return {
            "room": area.extra["room_name"],
            "x": node.extra["x"],
            "y": node.extra["y"],
        }

    def _create_pickup_config(
        self, pickup_list: list[ExportedPickupDetails], model_data: dict[str, dict[str, Any]]
    ) -> dict:
        items = []
        for pickup in pickup_list:
            data = model_data[pickup.name]
            if pickup.conditional_resources[0].resources:
                quantity = pickup.conditional_resources[0].resources[0][1]
            else:
                quantity = 1

            desc: str = data["description"]
            desc = desc.replace("{COUNT}", str(quantity))

            pickup_entry = {
                "pickup_index": pickup.index.index,
                "item_key": data["item_key"],
                "item_val": quantity,
                "item_display_name": data["display_name"],
                "item_description": desc,
                "aeons": data.get("default_aeons", []),
                "sprite": data["sprite"],
                "fanfare": data["fanfare"],
            }

            if "artifact_idx" in data:
                pickup_entry["artifact_idx"] = data["artifact_idx"]

            if pickup.name == "Missile Expansion":
                pickup_entry["additional_items"] = {"Missiles": f'ds_zero("Missiles") + {quantity}'}
            if pickup.name == "Power Bomb Expansion":
                pickup_entry["additional_items"] = {"Power Bombs": f'ds_zero("Power Bombs") + {quantity}'}
            if pickup.name == "Energy Tank":
                pickup_entry["additional_items"] = {
                    "Energy Tanks": 'ds_zero("Energy Tanks Max")',
                    "Energy": "99",
                }
            items.append(pickup_entry)

        return {
            "items": items,
            "require_main_missiles": False,
            "require_pb_detonator": False,
            "require_power_beam": False,
        }

    def create_game_specific_data(self, randovania_meta: PatcherDataMeta) -> dict:
        model_data = typing.cast(
            "dict[str, dict[str, Any]]",
            json_lib.read_path(RandovaniaGame.PRIME_ORIGINS.data_path.joinpath("pickup_database", "model-data.json")),
        )

        pickup_list = self.export_pickup_list()

        return {
            "identifier": self._create_identifier(),
            "starting_items": self._create_starting_items(),
            "starting_location": self._create_starting_location(),
            "pickups": self._create_pickup_config(pickup_list, model_data),
        }

    @override
    @classmethod
    def hint_namer_type(cls) -> type[HintNamer]:
        return MPOHintNamer
