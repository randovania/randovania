from __future__ import annotations

import dataclasses
from enum import Enum
from typing import TYPE_CHECKING

from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.game_description import default_database
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.game import RandovaniaGame
from randovania.layout.lib import location_list
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node


class TeleporterShuffleMode(BitPackEnum, Enum):
    long_name: str
    description: str

    VANILLA = "vanilla"
    ECHOES_SHUFFLED = "echoes-shuffled"
    TWO_WAY_RANDOMIZED = "randomized"
    TWO_WAY_UNCHECKED = "two-way-unchecked"
    ONE_WAY_TELEPORTER = "one-way-teleporter"
    ONE_WAY_TELEPORTER_REPLACEMENT = "one-way-teleporter-replacement"
    ONE_WAY_ANYTHING = "one-way-anything"


enum_lib.add_long_name(
    TeleporterShuffleMode,
    {
        TeleporterShuffleMode.VANILLA: "Original connections",
        TeleporterShuffleMode.ECHOES_SHUFFLED: "Shuffle regions",
        TeleporterShuffleMode.TWO_WAY_RANDOMIZED: "Two-way, between regions",
        TeleporterShuffleMode.TWO_WAY_UNCHECKED: "Two-way, unchecked",
        TeleporterShuffleMode.ONE_WAY_TELEPORTER: "One-way, with cycles",
        TeleporterShuffleMode.ONE_WAY_TELEPORTER_REPLACEMENT: "One-way, with replacement",
        TeleporterShuffleMode.ONE_WAY_ANYTHING: "One-way, anywhere",
    },
)


class TeleporterList(location_list.LocationList):
    @classmethod
    def nodes_list(cls, game: RandovaniaGame) -> list[NodeIdentifier]:
        game_description = default_database.game_description_for(game)
        teleporter_dock_types = game_description.dock_weakness_database.all_teleporter_dock_types
        region_list = game_description.region_list
        nodes = [
            node.identifier
            for node in region_list.all_nodes
            if isinstance(node, DockNode) and node.dock_type in teleporter_dock_types
        ]
        nodes.sort()
        return nodes

    @classmethod
    def element_type(cls):
        return NodeIdentifier

    def ensure_has_locations(self, area_locations: list[NodeIdentifier], enabled: bool) -> TeleporterList:
        return super().ensure_has_locations(area_locations, enabled)


def _valid_teleporter_target(area: Area, node: Node, game: RandovaniaGame):
    if (
        game in (RandovaniaGame.METROID_PRIME, RandovaniaGame.METROID_PRIME_ECHOES)
        and area.name == "Credits"
        and node.name in ("Event - Credits", "Event - Dark Samus 3 and 4")
    ):
        return True

    if any(node.name == "Save Station" for node in area.nodes):
        return False

    return node.valid_starting_location and not node.is_derived_node


class TeleporterTargetList(location_list.LocationList):
    @classmethod
    def nodes_list(cls, game: RandovaniaGame):
        return location_list.node_and_area_with_filter(
            game, lambda area, node: _valid_teleporter_target(area, node, game)
        )


@dataclasses.dataclass(frozen=True)
class TeleporterConfiguration(BitPackDataclass, JsonDataclass, DataclassPostInitTypeCheck):
    mode: TeleporterShuffleMode
    excluded_teleporters: TeleporterList
    excluded_targets: TeleporterTargetList

    @property
    def game(self) -> RandovaniaGame:
        return self.excluded_teleporters.game

    @property
    def is_vanilla(self):
        return self.mode == TeleporterShuffleMode.VANILLA

    @property
    def has_shuffled_target(self):
        return self.mode == TeleporterShuffleMode.ONE_WAY_ANYTHING

    @property
    def editable_teleporters(self) -> list[NodeIdentifier]:
        return [
            teleporter
            for teleporter in self.excluded_teleporters.nodes_list(self.game)
            if teleporter not in self.excluded_teleporters.locations
        ]

    @property
    def valid_targets(self) -> list[NodeIdentifier]:
        if self.mode == TeleporterShuffleMode.ONE_WAY_ANYTHING:
            return [
                location
                for location in self.excluded_targets.nodes_list(self.game)
                if location not in self.excluded_targets.locations
            ]

        elif self.mode in {
            TeleporterShuffleMode.ONE_WAY_TELEPORTER,
            TeleporterShuffleMode.ONE_WAY_TELEPORTER_REPLACEMENT,
        }:
            game_description = default_database.game_description_for(self.game)
            teleporter_dock_types = game_description.dock_weakness_database.all_teleporter_dock_types
            region_list = game_description.region_list

            result = []
            for identifier in self.editable_teleporters:
                node = region_list.node_by_identifier(identifier)
                if isinstance(node, DockNode) and node.dock_type in teleporter_dock_types:
                    # Valid destinations must be valid starting areas
                    area = region_list.nodes_to_area(node)
                    if area.has_start_node():
                        result.append(identifier)
                    # Hack for Metroid Prime 1, where the scripting for Metroid Prime Lair is dependent
                    # on the previous room
                    elif area.name == "Metroid Prime Lair":
                        result.append(
                            NodeIdentifier.create("Impact Crater", "Subchamber Five", "Dock to Subchamber Four")
                        )
            return result
        else:
            return []

    @property
    def static_teleporters(self) -> dict[NodeIdentifier, NodeIdentifier]:
        return {}

    def description(self, teleporter_name: str):
        result = []
        if self.mode not in {TeleporterShuffleMode.VANILLA, TeleporterShuffleMode.ECHOES_SHUFFLED}:
            if not self.is_vanilla and self.excluded_teleporters.locations:
                result.append(f"{len(self.excluded_teleporters.locations)} {teleporter_name}")

            if self.has_shuffled_target and self.excluded_targets.locations:
                result.append(f"{len(self.excluded_targets.locations)} targets")

        if result:
            return f"{self.mode.long_name}; excluded {', '.join(result)}"
        else:
            return self.mode.long_name

    def dangerous_settings(self):
        if self.mode == TeleporterShuffleMode.ONE_WAY_ANYTHING:
            return ["One-way anywhere teleporters"]
        return []
