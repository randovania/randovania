from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Final, override

from randovania.exporter.hints import guaranteed_item_hint
from randovania.exporter.hints.joke_hints import GENERIC_JOKE_HINTS
from randovania.exporter.patch_data_factory import PatchDataFactory, PatcherDataMeta
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.games.prime_hunters.exporter.hint_namer import HuntersHintNamer
from randovania.games.prime_hunters.layout import HuntersConfiguration, HuntersCosmeticPatches
from randovania.games.prime_hunters.layout.force_field_configuration import LayoutForceFieldRequirement
from randovania.generator.pickup_pool import pickup_creator
from randovania.layout.base.hint_configuration import SpecificPickupHintMode

if TYPE_CHECKING:
    from randovania.exporter.hints.hint_namer import HintNamer
    from randovania.game_description.db.area import Area
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_collection import ResourceCollection


def item_id_for_item_resource(resource: ItemResourceInfo) -> int:
    return resource.extra["weapon_id"]


def force_field_index_for_requirement(game: GameDescription, requirement: LayoutForceFieldRequirement) -> int:
    return item_id_for_item_resource(game.resource_database.get_item(requirement.item_name))


ITEM_SPAWN_ENTITY_TYPE: Final = 4
ARTIFACT_ENTITY_TYPE: Final = 17
OCTOLITH_MODEL_ID: Final = 8
NOTHING_ITEM_TYPE: Final = 21

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

_STRING_ID_TO_SCAN_TITLE = {
    "904L": "OCTOLITH HINTS 01",
    "014L": "OCTOLITH HINTS 02",
    "114L": "OCTOLITH HINTS 03",
    "214L": "OCTOLITH HINTS 04",
}


class HuntersPatchDataFactory(PatchDataFactory[HuntersConfiguration, HuntersCosmeticPatches]):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_HUNTERS

    def _calculate_starting_inventory(self, resources: ResourceCollection) -> dict[str, str | int]:
        result: dict[str, str | int] = {}

        starting_items: defaultdict = defaultdict(int)
        starting_items.update({resource.long_name: quantity for resource, quantity in resources.as_resource_gain()})

        def starts_with_item(weapon_name: str) -> bool:
            return starting_items[weapon_name] > 0

        fmt = "{:d}" * 8  # 8-bit bitfield

        weapons = [
            starts_with_item("Shock Coil"),
            starts_with_item("Magmaul"),
            starts_with_item("Judicator"),
            starts_with_item("Imperialist"),
            starts_with_item("Battlehammer"),
            True,  # Missiles
            starts_with_item("Volt Driver"),
            True,  # Power Beam
        ]

        octoliths = []
        for i in reversed(range(1, 9)):
            octoliths.append(starts_with_item(f"Octolith {i}"))

        result["weapons"] = fmt.format(*weapons)
        result["missiles"] = starting_items["Missiles"]
        result["ammo"] = 40
        result["energy_tanks"] = starting_items["Energy Tank"]
        result["octoliths"] = fmt.format(*octoliths)

        return result

    def _get_pickups_for_area(self, area: Area) -> list:
        pickups = []
        pickup_nodes_gen = (node for node in area.nodes if isinstance(node, PickupNode))
        pickup_nodes = sorted(pickup_nodes_gen, key=lambda n: n.pickup_index)

        for node in pickup_nodes:
            target = self.patches.pickup_assignment.get(node.pickup_index, None)
            pickup: dict = {}

            pickup["entity_id"] = node.extra["entity_id"]

            if target is None:
                pickup["entity_type"] = ITEM_SPAWN_ENTITY_TYPE
                pickup["item_type"] = NOTHING_ITEM_TYPE
            else:
                entity_type = target.pickup.extra["entity_type"]
                if entity_type == ITEM_SPAWN_ENTITY_TYPE:
                    pickup["entity_type"] = ITEM_SPAWN_ENTITY_TYPE
                    pickup["item_type"] = target.pickup.extra["item_type"]
                else:
                    pickup["entity_type"] = ARTIFACT_ENTITY_TYPE
                    model_id = target.pickup.extra.get("model_id", None)
                    if model_id == OCTOLITH_MODEL_ID:
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
                "entity_id": self.game.region_list.node_by_identifier(node_identifier).extra["entity_id"],
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

    def _encode_hints(self) -> list[dict]:
        exporter = self.get_hint_exporter(
            self.description.all_patches, self.players_config, self.rng, GENERIC_JOKE_HINTS
        )

        octoliths = [self.game.resource_database.get_item(f"Octolith{i + 1}") for i in range(8)]
        octoliths_precision = self.configuration.hints.specific_pickup_hints["octoliths"]

        if octoliths_precision != SpecificPickupHintMode.DISABLED:
            octolith_hint_mapping = guaranteed_item_hint.create_guaranteed_hints_for_resources(
                self.description.all_patches,
                self.players_config,
                exporter.namer,
                True if octoliths_precision == SpecificPickupHintMode.HIDE_AREA else False,
                octoliths,
                False,
            )

        hints: list = []

        hint_nodes = sorted(self.game.region_list.iterate_nodes_of_type(HintNode))

        i = 1
        for node in hint_nodes:
            hint_dict = {}
            string_id = node.extra["entity_type_data"]["string_id"]
            hint_dict["string_id"] = string_id

            scan_title = f"{_STRING_ID_TO_SCAN_TITLE[string_id]}\\"
            scan_text = " ".join(
                [
                    text
                    for text in octolith_hint_mapping.values()
                    if f"OCTOLITH {i}" in text or f"OCTOLITH {i + 1}" in text
                ]
            )

            dud_hint = "this lore scan did not provide any useful OCTOLITH hints."
            useless_hints = [self.rng.choice(GENERIC_JOKE_HINTS + [dud_hint])]

            if octoliths_precision != SpecificPickupHintMode.DISABLED:
                if scan_text == "":
                    hint_dict["string"] = scan_title + self.rng.choice(useless_hints).lower()
                else:
                    hint_dict["string"] = scan_title + scan_text

                if not self.configuration.octoliths.placed_octoliths:
                    hint_dict["string"] = "the OCTOLITHS have already been found. there is no need to locate them."
            else:
                hint_dict["string"] = scan_title + self.rng.choice(useless_hints).lower()

            hints.append(hint_dict)

            i += 2

        return hints

    def create_visual_nothing(self) -> PickupEntry:
        """The model of this pickup replaces the model of all pickups when PickupModelDataSource is ETM"""
        return pickup_creator.create_visual_nothing(self.game_enum(), "Nothing")

    def create_game_specific_data(self, randovania_meta: PatcherDataMeta) -> dict:
        starting_items = self._calculate_starting_inventory(self.patches.starting_resources())
        return {
            "starting_items": starting_items,
            "areas": self._entity_patching_per_area(),
            "hints": self._encode_hints(),
        }

    @override
    @classmethod
    def hint_namer_type(cls) -> type[HintNamer]:
        return HuntersHintNamer
