from __future__ import annotations

import functools
from collections import defaultdict
from collections.abc import Iterable
from typing import TYPE_CHECKING, Literal, override

from randovania.exporter import pickup_exporter
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.region import Region
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.games.prime2.exporter.patch_data_factory import (
    default_prime2_memo_data,
    echoes_raw_pickup_list,
    simplified_prime2_memo_data,
)
from randovania.games.prime2_opr.exporter.hint_namer import EchoesOPRHintNamer
from randovania.games.prime2_opr.layout import EchoesOPRConfiguration, EchoesOPRCosmeticPatches
from randovania.lib import frozen_lib

if TYPE_CHECKING:
    from randovania.exporter.hints.hint_namer import HintNamer
    from randovania.exporter.patch_data_factory import PatcherDataMeta


type SoundType = Literal["standard", "expansion", "key"]


class EchoesOPRPatchDataFactory(PatchDataFactory[EchoesOPRConfiguration, EchoesOPRCosmeticPatches]):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_ECHOES_OPR

    def create_game_specific_data(self, randovania_meta: PatcherDataMeta) -> dict:
        # header data
        data = {
            "title_screen_text": "",
            "game_title": f"Echoes OPR - {self.description.shareable_word_hash}"[:64],
            "seed": self.description.get_seed_for_world(self.players_config.player_index),
            "world_uuid": str(self.players_config.get_own_uuid()),
        }

        # starting location/items
        data["starting_area"] = self._area_reference_from_identifier(self.patches.starting_location.area_identifier)
        data["starting_items"] = self.create_starting_items_data()

        # world changes
        data["world_changes"] = self.create_world_changes()

        return data

    @override
    @classmethod
    def hint_namer_type(cls) -> type[HintNamer]:
        return EchoesOPRHintNamer

    def _asset_id_for_region(self, region: Region) -> int:
        if "asset_id" in region.extra:
            return region.extra["asset_id"]
        else:
            light_region = self.game.region_list.region_with_name(region.extra["associated_region"])
            return light_region.extra["asset_id"]

    def _asset_ids_for_area(self, identifier: AreaIdentifier) -> tuple[int, int]:
        region, area = self.game.region_list.region_and_area_by_area_identifier(identifier)
        return self._asset_id_for_region(region), area.extra["asset_id"]

    def _area_reference_from_identifier(self, identifier: AreaIdentifier) -> dict:
        mlvl_id, mrea_id = self._asset_ids_for_area(identifier)
        return {
            "mlvl_id": mlvl_id,
            "mrea_id": mrea_id,
        }

    def create_starting_items_data(self) -> list[dict]:
        result = []

        for item, amount in self.patches.starting_resources().as_resource_gain():
            assert isinstance(item, ItemResourceInfo)
            item_id = item.extra["item_id"]

            result.append(
                {
                    "item": item_id,
                    "capacity": amount,
                }
            )

        return result

    def create_world_changes(self) -> list[dict]:
        def _area_change():
            return {
                "pickups": [],
                "translator_gates": [],
                "door_locks": [],
            }

        area_changes: dict[tuple[int, int], dict] = defaultdict(_area_change)

        for mlvl_id, mrea_id, pickup in self.create_pickups():
            area_changes[mlvl_id, mrea_id]["pickups"].append(pickup)

        for mlvl_id, mrea_id, gate in self.create_translator_gates():
            area_changes[mlvl_id, mrea_id]["translator_gates"].append(gate)

        for mlvl_id, mrea_id, door_lock in self.create_door_locks():
            area_changes[mlvl_id, mrea_id]["door_locks"].append(door_lock)

        world_changes: dict[int, list] = defaultdict(list)
        for (mlvl_id, mrea_id), area_change in area_changes.items():
            world_changes[mlvl_id].append(
                {
                    "mrea_id": mrea_id,
                    **area_change,
                }
            )

        return [
            {
                "mlvl_id": mlvl_id,
                "area_changes": world_area_changes,
            }
            for mlvl_id, world_area_changes in world_changes.items()
        ]

    def _get_memo_data(self) -> dict[str, str]:
        if self.cosmetic_patches.disable_hud_popup:
            return simplified_prime2_memo_data()

        else:
            result = default_prime2_memo_data()

            # TODO: add preset settings for this and adjust dynamically
            result["Massive Damage"] = "Massive Damage acquired!\nDamage dealt increased by 100%."

            return result

    @functools.cached_property
    def sound_data(self) -> dict[SoundType, int]:
        return {
            "standard": 10057,
            "expansion": 10057,
            "key": 1075,
        }

    @functools.cached_property
    def jingle_data(self) -> dict[SoundType, dict]:
        return {
            "standard": {"file_name": "/audio/itm_x_long_00.dsp", "volume": 71},
            "expansion": {"file_name": "/audio/itm_x_short_00.dsp", "volume": 55},
            "key": {"file_name": "/audio/skytenkey-jin-short32.dsp", "volume": 110},
        }

    def _get_sound_type(self, model_name: str) -> SoundType:
        sound_type: SoundType = "standard"

        if model_name in {
            "SkyTempleKey",
            "DarkTempleKey",
            # "AgonTempleKey",
            # "TorvusTempleKey",
            # "HiveTempleKey",
            "EnergyTransferModule",
        }:
            sound_type = "key"

        elif model_name in {
            "MissileExpansion",
            "MissileExpansionLarge",
            "MissileExpansionPrime1",
            "PowerBombExpansion",
            "DarkBeamAmmoExpansion",
            "LightBeamAmmoExpansion",
            "BeamAmmoExpansion",
            "EnergyTank",
            "EnergyTankSmall",
        }:
            sound_type = "expansion"

        return sound_type

    def _get_pickup_appearance(self, exported_pickup: pickup_exporter.ExportedPickupDetails, index: int) -> dict:
        progressive_models = {
            "ProgressiveSuit": ("DarkSuit", "LightSuit"),
            "ProgressiveGrapple": ("GrappleBeam", "ScrewAttack"),
        }
        offworld_progressive = {
            "ProgressiveSuit": "VariaSuit",
            "ProgressiveGrapple": "GrappleBeam",
        }

        model_name = exported_pickup.model.name
        scan = f"{exported_pickup.name}. {exported_pickup.description}".strip()

        if model_name in progressive_models and exported_pickup.model == exported_pickup.original_model:
            if exported_pickup.is_for_remote_player:
                model_name = offworld_progressive[model_name]
            else:
                model_name = progressive_models[model_name][index]

                name = exported_pickup.conditional_resources[index].name
                scan = f"{name}."

        sound_type = self._get_sound_type(model_name)

        return {
            "model_data": model_name,
            "sound": self.sound_data[sound_type],
            "jingle": self.jingle_data[sound_type],
            "hud_text": exported_pickup.collection_text[index],
            "scan": scan,
        }

    def _get_pickup_resources(self, exported_pickup: pickup_exporter.ExportedPickupDetails, index: int) -> list[dict]:
        # TODO: multiworld

        conditional = exported_pickup.conditional_resources[index]

        return [
            {
                "item": resource.extra["item_id"],
                "amount": quantity,
            }
            for resource, quantity in conditional.resources
            if quantity != 0
        ]

    def _get_pickup_stage(self, exported_pickup: pickup_exporter.ExportedPickupDetails, index: int) -> dict:
        return {
            "resources": self._get_pickup_resources(exported_pickup, index),
            "appearance": self._get_pickup_appearance(exported_pickup, index),
            "conversion": [
                {
                    "from_item": conversion.source.extra["item_id"],
                    "to_item": conversion.target.extra["item_id"],
                }
                for conversion in exported_pickup.conversion
            ],
        }

    def _get_location_data(self, pickup_node: PickupNode) -> dict:
        result = {}
        result.update(frozen_lib.unwrap(pickup_node.extra["location_data"]))
        if "instances" in result:
            result.update(result.pop("instances"))

        if "connections" in result:
            for con in result["connections"]:
                con["state"] = "ZERO"

        if result["type"] == "custom":
            assert pickup_node.location is not None
            result["position"] = {
                "x": pickup_node.location.x,
                "y": pickup_node.location.y,
                "z": pickup_node.location.z,
            }

        return result

    def create_pickups(self) -> Iterable[tuple[int, int, dict]]:
        pickup_list = echoes_raw_pickup_list(
            self._get_memo_data(),
            self.configuration,
            self.game,
            self.patches,
            self.players_config,
            self.rng,
        )

        for exported_pickup in pickup_list:
            pickup_node = self.game.region_list.node_from_pickup_index(exported_pickup.index)
            mlvl, mrea = self._asset_ids_for_area(pickup_node.identifier.area_identifier)

            pickup = {
                "location": self._get_location_data(pickup_node),
                "primary_stage": self._get_pickup_stage(exported_pickup, 0),
                "progressive_stages": [
                    {
                        **self._get_pickup_stage(exported_pickup, i + 1),
                        "required_item": conditional.item.extra["item_id"],
                    }
                    for i, conditional in enumerate(exported_pickup.conditional_resources[1:])
                ],
            }
            yield mlvl, mrea, pickup

    def create_translator_gates(self) -> Iterable[tuple[int, int, dict]]:
        for identifier, requirement in self.patches.game_specific["translator_gates"].items():
            node = self.game.region_list.node_by_identifier(NodeIdentifier.from_string(identifier))
            mlvl, mrea = self._asset_ids_for_area(node.identifier.area_identifier)

            if requirement == "removed":
                requirement = "unlocked"

            gate = {
                "translator": requirement,
                **node.extra.get("gate_instances", {}),
            }
            yield mlvl, mrea, gate

    def create_door_locks(self) -> Iterable[tuple[int, int, dict]]:
        for dock, weakness in self.patches.all_dock_weaknesses(self.game):
            mlvl, mrea = self._asset_ids_for_area(dock.identifier.area_identifier)

            door_lock = {
                "dock_name": dock.extra["dock_name"],
                "old_door_type": dock.default_dock_weakness.extra["door_type"],
                "new_door_type": weakness.extra["door_type"],
            }

            yield mlvl, mrea, door_lock
