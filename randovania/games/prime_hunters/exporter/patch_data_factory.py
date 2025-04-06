from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.games.prime_hunters.exporter.hint_namer import HuntersHintNamer
from randovania.games.prime_hunters.layout import HuntersConfiguration, HuntersCosmeticPatches
from randovania.games.prime_hunters.layout.force_field_configuration import LayoutForceFieldRequirement

if TYPE_CHECKING:
    from randovania.exporter.hints.hint_namer import HintNamer
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_collection import ResourceCollection


def item_id_for_item_resource(resource: ItemResourceInfo) -> int:
    return resource.extra["weapon_id"]


def force_field_index_for_requirement(game: GameDescription, requirement: LayoutForceFieldRequirement) -> int:
    return item_id_for_item_resource(game.resource_database.get_item(requirement.item_name))


def _create_force_fields_field(game: GameDescription, game_specific: dict[str, str]) -> list:
    """
    Creates the force field entries in the patcher file
    :return:
    """
    regions = list(game.region_list.regions)
    for region in regions:
        for area in region.areas:
            force_fields = [
                {
                    "region": region.name,
                    "room": area.name,
                    "entity_id": game.region_list.node_by_identifier(NodeIdentifier.from_string(identifier)).extra[
                        "entity_id"
                    ],
                    "type": force_field_index_for_requirement(game, LayoutForceFieldRequirement(requirement)),
                }
                for identifier, requirement in game_specific.items()
            ]

    return force_fields


_ARTIFACT_TO_MODEL_ID = {
    "AlinosArtifact1": 0,
    "AlinosArtifact2": 1,
    "CelestialArtifact1": 2,
    "CelestialArtifact2": 3,
    "VDOArtifact1": 4,
    "VDOArtifact2": 5,
    "ArcterraArtifact1": 6,
    "ArcterraArtifact2": 7,
}

_OCTOLITH_TO_ARTIFACT_ID = {
    "Octolith1": 0,
    "Octolith2": 1,
    "Octolith3": 2,
    "Octolith4": 3,
    "Octolith5": 4,
    "Octolith6": 5,
    "Octolith7": 6,
    "Octolith8": 7,
}


class HuntersPatchDataFactory(PatchDataFactory[HuntersConfiguration, HuntersCosmeticPatches]):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_HUNTERS

    def _calculate_starting_inventory(self, resources: ResourceCollection) -> dict[str, str]:
        result = {
            "weapons_string": "00000101",
        }
        return result

    def _entity_patching_per_area(self) -> dict:
        db = self.game
        regions = list(db.region_list.regions)

        # Initialize serialized db data
        level_data: dict = {}

        for region in regions:
            level_data[region.name] = {
                "levels": {},
            }

            for area in region.areas:
                level_data[region.name]["levels"][area.name] = {
                    "pickups": [],
                    "force_fields": [],
                }

        # serialize pickup modifications
        for region in regions:
            for area in region.areas:
                pickup_nodes_gen = (node for node in area.nodes if isinstance(node, PickupNode))
                pickup_nodes = sorted(pickup_nodes_gen, key=lambda n: n.pickup_index)
                for node in pickup_nodes:
                    target = self.patches.pickup_assignment.get(node.pickup_index, None)

                    assert target is not None

                    pickup: dict = {}
                    pickup["entity_id"] = node.extra["entity_id"]
                    entity_type = target.pickup.extra["entity_type"]

                    if entity_type == 4:
                        pickup["entity_type"] = 4
                        pickup["item_type"] = target.pickup.extra["item_type"]
                    else:
                        pickup["entity_type"] = 17
                        model_id = target.pickup.extra.get("model_id", None)
                        if model_id == 8:
                            pickup["model_id"] = model_id
                            pickup["artifact_id"] = _OCTOLITH_TO_ARTIFACT_ID[target.pickup.model.name]
                        else:
                            pickup["model_id"] = _ARTIFACT_TO_MODEL_ID[target.pickup.model.name]
                            pickup["artifact_id"] = target.pickup.extra["artifact_id"]

                    level_data[region.name]["levels"][area.name]["pickups"].append(pickup)

        # serialize force field modifications
        force_fields = _create_force_fields_field(self.game, self.patches.game_specific["force_fields"])
        for force_field in force_fields:
            for region in regions:
                for area in region.areas:
                    if force_field["room"] == area.name:
                        level_data[region.name]["levels"][force_field["room"]]["force_fields"].append(force_field)

        return level_data

    def create_game_specific_data(self) -> dict:
        starting_items = self._calculate_starting_inventory(self.patches.starting_resources())
        return {
            "starting_items": starting_items,
            "areas": self._entity_patching_per_area(),
        }

    @override
    @classmethod
    def hint_namer_type(cls) -> type[HintNamer]:
        return HuntersHintNamer
