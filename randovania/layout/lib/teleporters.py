import dataclasses
from enum import Enum
from typing import Dict, List

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.game_description import default_database
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.world.node import TeleporterNode
from randovania.game_description.world.teleporter import Teleporter
from randovania.games.game import RandovaniaGame
from randovania.layout.lib import location_list


class TeleporterShuffleMode(BitPackEnum, Enum):
    VANILLA = "vanilla"
    TWO_WAY_RANDOMIZED = "randomized"
    TWO_WAY_UNCHECKED = "two-way-unchecked"
    ONE_WAY_ELEVATOR = "one-way-elevator"
    ONE_WAY_ELEVATOR_REPLACEMENT = "one-way-elevator-replacement"
    ONE_WAY_ANYTHING = "one-way-anything"

    @property
    def long_name(self) -> str:
        if self == TeleporterShuffleMode.VANILLA:
            return "Original connections"
        elif self == TeleporterShuffleMode.TWO_WAY_RANDOMIZED:
            return "Two-way, between areas"
        elif self == TeleporterShuffleMode.TWO_WAY_UNCHECKED:
            return "Two-way, unchecked"
        elif self == TeleporterShuffleMode.ONE_WAY_ELEVATOR:
            return "One-way, elevator room with cycles"
        elif self == TeleporterShuffleMode.ONE_WAY_ELEVATOR_REPLACEMENT:
            return "One-way, elevator room with replacement"
        elif self == TeleporterShuffleMode.ONE_WAY_ANYTHING:
            return "One-way, anywhere"
        else:
            raise ValueError(f"Unknown value: {self}")


def _has_editable_teleporter(area: Area) -> bool:
    return any(
        node.editable
        for node in area.nodes
        if isinstance(node, TeleporterNode)
    )


class TeleporterList(location_list.LocationList):
    @classmethod
    def areas_list(cls, game: RandovaniaGame) -> List[Teleporter]:
        world_list = default_database.game_description_for(game).world_list
        areas = [
            node.teleporter
            for world in world_list.worlds
            for area in world.areas
            for node in area.nodes
            if isinstance(node, TeleporterNode) and node.editable
        ]
        areas.sort()
        return areas

    @classmethod
    def element_type(cls):
        return Teleporter

    def ensure_has_location(self, area_location: Teleporter, enabled: bool) -> "TeleporterList":
        return super().ensure_has_location(area_location, enabled)

    def ensure_has_locations(self, area_locations: List[AreaLocation], enabled: bool) -> "TeleporterList":
        return super().ensure_has_locations(area_locations, enabled)


def _valid_teleporter_target(area: Area, game: RandovaniaGame):
    if game == RandovaniaGame.METROID_PRIME and area.area_asset_id == 3031702600:
        return True

    if game == RandovaniaGame.METROID_PRIME_ECHOES and area.area_asset_id == 1393588666:
        return True

    has_save_station = any(node.name == "Save Station" for node in area.nodes)
    return area.valid_starting_location and area.default_node_index is not None and not has_save_station


class TeleporterTargetList(location_list.LocationList):
    @classmethod
    def areas_list(cls, game: RandovaniaGame):
        return location_list.area_locations_with_filter(game, lambda area: _valid_teleporter_target(area, game))


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
    def editable_teleporters(self) -> List[Teleporter]:
        return [teleporter for teleporter in self.excluded_teleporters.areas_list(self.game)
                if teleporter not in self.excluded_teleporters.locations]

    @property
    def static_teleporters(self) -> Dict[Teleporter, AreaLocation]:
        static = {}
        if self.skip_final_bosses:
            if self.game == RandovaniaGame.METROID_PRIME:
                static[Teleporter(972217896, 597223686, 1049306)] = AreaLocation(0x13d79165, 0xb4b41c48)
            elif self.game == RandovaniaGame.METROID_PRIME_ECHOES:
                static[Teleporter(1006255871, 2278776548, 136970379)] = AreaLocation(1006255871, 1393588666)
            else:
                raise ValueError(f"Unsupported skip_final_bosses and {self.game}")

        return static

    @property
    def valid_targets(self) -> List[AreaLocation]:
        if self.mode == TeleporterShuffleMode.ONE_WAY_ANYTHING:
            return [location for location in self.excluded_targets.areas_list(self.game)
                    if location not in self.excluded_targets.locations]

        elif self.mode in {TeleporterShuffleMode.ONE_WAY_ELEVATOR, TeleporterShuffleMode.ONE_WAY_ELEVATOR_REPLACEMENT}:
            world_list = default_database.game_description_for(self.game).world_list
            return [
                world_list.teleporter_to_node(teleporter).default_connection
                for teleporter in self.editable_teleporters
            ]
        else:
            return []

    def description(self):
        result = []
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
