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
    from randovania.game_description.db.area import Area
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_collection import ResourceCollection


def item_id_for_item_resource(resource: ItemResourceInfo) -> int:
    return resource.extra["weapon_id"]


def force_field_index_for_requirement(game: GameDescription, requirement: LayoutForceFieldRequirement) -> int:
    return item_id_for_item_resource(game.resource_database.get_item(requirement.item_name))


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

    def _get_pickups_for_area(self, area: Area) -> list:
        pickups = []
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
            pickups.append(pickup)

        return pickups

    def _get_force_fields_for_area(self, area: Area, game_specific: dict) -> list:
        force_fields = []

        for identifier, requirement in game_specific.items():
            node_identifier = NodeIdentifier.from_string(identifier)
            if node_identifier.area != area.name:
                continue

            field = {
                "entity_id": self.game.region_list.node_by_identifier(NodeIdentifier.from_string(identifier)).extra[
                    "entity_id"
                ],
                "type": force_field_index_for_requirement(self.game, LayoutForceFieldRequirement(requirement)),
            }
            force_fields.append(field)

        return force_fields

    def _entity_patching_per_area(self) -> dict:
        db = self.game
        regions = list(db.region_list.regions)
        level_data: dict = {}

        for region in regions:
            level_data[region.name] = {
                "levels": {},
            }

            for area in region.areas:
                level_data[region.name]["levels"][area.name] = {
                    "pickups": self._get_pickups_for_area(area),
                    "force_fields": self._get_force_fields_for_area(area, self.patches.game_specific["force_fields"]),
                }

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
