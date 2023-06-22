import dataclasses
from enum import Enum

import randovania
from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.game_description import default_database
from randovania.game_description.db.area import Area
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.node import Node
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.teleporter_node import TeleporterNode
from randovania.games.game import RandovaniaGame
from randovania.layout.lib import location_list
from randovania.lib import enum_lib


class TeleporterShuffleMode(BitPackEnum, Enum):
    long_name: str
    description: str

    VANILLA = "vanilla"
    ECHOES_SHUFFLED = "echoes-shuffled"
    TWO_WAY_RANDOMIZED = "randomized"
    TWO_WAY_UNCHECKED = "two-way-unchecked"
    ONE_WAY_ELEVATOR = "one-way-elevator"
    ONE_WAY_ELEVATOR_REPLACEMENT = "one-way-elevator-replacement"
    ONE_WAY_ANYTHING = "one-way-anything"

    def usable_by_game(self, game: RandovaniaGame):
        if self != TeleporterShuffleMode.ECHOES_SHUFFLED:
            return True
        else:
            return game == RandovaniaGame.METROID_PRIME_ECHOES


enum_lib.add_long_name(TeleporterShuffleMode, {
    TeleporterShuffleMode.VANILLA: "Original connections",
    TeleporterShuffleMode.ECHOES_SHUFFLED: "Shuffle regions",
    TeleporterShuffleMode.TWO_WAY_RANDOMIZED: "Two-way, between regions",
    TeleporterShuffleMode.TWO_WAY_UNCHECKED: "Two-way, unchecked",
    TeleporterShuffleMode.ONE_WAY_ELEVATOR: "One-way, elevator room with cycles",
    TeleporterShuffleMode.ONE_WAY_ELEVATOR_REPLACEMENT: "One-way, elevator room with replacement",
    TeleporterShuffleMode.ONE_WAY_ANYTHING: "One-way, anywhere",
})

enum_lib.add_per_enum_field(TeleporterShuffleMode, "description", {
    TeleporterShuffleMode.VANILLA:
        "all elevators are connected to where they do in the original game.",
    TeleporterShuffleMode.ECHOES_SHUFFLED:
        "keeps Temple Grounds in place, shuffling the locations of all other regions with each other."
        f"<p><img src=\"{randovania.get_data_path()}/gui_assets/echoes_elevator_map.png\" width=450/></p>",
    TeleporterShuffleMode.TWO_WAY_RANDOMIZED:
        "after taking an elevator, the elevator in the room you are in will bring you back to where you were. "
        "An elevator will never connect to another in the same region. "
        "This is the only setting that guarantees all regions are reachable.",
    TeleporterShuffleMode.TWO_WAY_UNCHECKED:
        "after taking an elevator, the elevator in the room you are in will bring you back to where you were.",
    TeleporterShuffleMode.ONE_WAY_ELEVATOR:
        "all elevators bring you to an elevator room, but going backwards can go somewhere else. "
        "All rooms are used as a destination exactly once, causing all elevators to be separated into loops.",
    TeleporterShuffleMode.ONE_WAY_ELEVATOR_REPLACEMENT:
        "all elevators bring you to an elevator room, but going backwards can go somewhere else. "
        "Rooms can be used as a destination multiple times, causing elevators which you can possibly not come back to.",
    TeleporterShuffleMode.ONE_WAY_ANYTHING:
        "elevators are connected to any room from the game.",
})


def _has_editable_teleporter(area: Area) -> bool:
    return any(
        node.editable
        for node in area.nodes
        if isinstance(node, TeleporterNode)
    )


class TeleporterList(location_list.LocationList):
    @classmethod
    def nodes_list(cls, game: RandovaniaGame) -> list[NodeIdentifier]:
        region_list = default_database.game_description_for(game).region_list
        nodes = [
            region_list.identifier_for_node(node)
            for node in region_list.all_nodes
            if isinstance(node, TeleporterNode) and node.editable
        ]
        nodes.sort()
        return nodes

    @classmethod
    def element_type(cls):
        return NodeIdentifier

    def ensure_has_location(self, area_location: NodeIdentifier, enabled: bool) -> "TeleporterList":
        return super().ensure_has_location(area_location, enabled)

    def ensure_has_locations(self, area_locations: list[NodeIdentifier], enabled: bool) -> "TeleporterList":
        return super().ensure_has_locations(area_locations, enabled)


def _valid_teleporter_target(area: Area, node: Node, game: RandovaniaGame):
    if (game in (RandovaniaGame.METROID_PRIME, RandovaniaGame.METROID_PRIME_ECHOES) and
            area.name == "Credits" and node.name == area.default_node):
        return True

    has_save_station = any(node.name == "Save Station" for node in area.nodes)
    return (area.has_start_node() and area.default_node is not None and
            area.default_node == node.name and not has_save_station)


class TeleporterTargetList(location_list.LocationList):
    @classmethod
    def nodes_list(cls, game: RandovaniaGame):
        return location_list.node_and_area_with_filter(
            game,
            lambda area, node: _valid_teleporter_target(area, node, game)
        )


@dataclasses.dataclass(frozen=True)
class TeleporterConfiguration(BitPackDataclass, JsonDataclass, DataclassPostInitTypeCheck):
    mode: TeleporterShuffleMode
    excluded_teleporters: TeleporterList
    excluded_targets: TeleporterTargetList
    skip_final_bosses: bool
    allow_unvisited_room_names: bool

    @property
    def game(self) -> RandovaniaGame:
        return self.excluded_teleporters.game

    @property
    def is_vanilla(self):
        return self.mode == TeleporterShuffleMode.VANILLA

    @property
    def can_use_unvisited_room_names(self) -> bool:
        return self.is_vanilla or self.allow_unvisited_room_names

    @property
    def has_shuffled_target(self):
        return self.mode == TeleporterShuffleMode.ONE_WAY_ANYTHING

    @property
    def editable_teleporters(self) -> list[NodeIdentifier]:
        return [teleporter for teleporter in self.excluded_teleporters.nodes_list(self.game)
                if teleporter not in self.excluded_teleporters.locations]

    @property
    def static_teleporters(self) -> dict[NodeIdentifier, AreaIdentifier]:
        static = {}
        if self.skip_final_bosses:
            if self.game == RandovaniaGame.METROID_PRIME:
                crater = NodeIdentifier.create("Tallon Overworld", "Artifact Temple",
                                               "Teleport to Impact Crater - Crater Impact Point")
                static[crater] = AreaIdentifier("End of Game", "Credits")
            elif self.game == RandovaniaGame.METROID_PRIME_ECHOES:
                gateway = NodeIdentifier.create("Temple Grounds", "Sky Temple Gateway",
                                                "Teleport to Great Temple - Sky Temple Energy Controller")
                static[gateway] = AreaIdentifier("Temple Grounds", "Credits")
            else:
                raise ValueError(f"Unsupported skip_final_bosses and {self.game}")

        return static

    @property
    def valid_targets(self) -> list[AreaIdentifier]:
        if self.mode == TeleporterShuffleMode.ONE_WAY_ANYTHING:
            return [location.area_identifier for location in self.excluded_targets.nodes_list(self.game)
                    if location not in self.excluded_targets.locations]

        elif self.mode in {TeleporterShuffleMode.ONE_WAY_ELEVATOR, TeleporterShuffleMode.ONE_WAY_ELEVATOR_REPLACEMENT}:
            region_list = default_database.game_description_for(self.game).region_list
            result = []
            for identifier in self.editable_teleporters:
                node = region_list.node_by_identifier(identifier)
                if isinstance(node, TeleporterNode) and node.editable:
                    # Valid destinations must be valid starting areas
                    area = region_list.nodes_to_area(node)
                    if area.has_start_node():
                        result.append(identifier.area_identifier)
                    # Hack for Metroid Prime 1, where the scripting for Metroid Prime Lair is dependent
                    # on the previous room
                    elif area.name == "Metroid Prime Lair":
                        result.append(AreaIdentifier.from_string("Impact Crater/Subchamber Five"))
            return result
        else:
            return []

    def description(self):
        result = []
        if self.mode not in {TeleporterShuffleMode.VANILLA, TeleporterShuffleMode.ECHOES_SHUFFLED}:
            if not self.is_vanilla and self.excluded_teleporters.locations:
                result.append(f"{len(self.excluded_teleporters.locations)} teleporters")

            if self.has_shuffled_target and self.excluded_targets.locations:
                result.append(f"{len(self.excluded_targets.locations)} targets")

        if result:
            return f"{self.mode.long_name}; excluded {', '.join(result)}"
        else:
            return self.mode.long_name

    def dangerous_settings(self):
        if self.mode == TeleporterShuffleMode.ONE_WAY_ANYTHING:
            return ["One-way anywhere elevators"]
        return []
