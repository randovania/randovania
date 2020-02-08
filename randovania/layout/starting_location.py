from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Union, Tuple, List, FrozenSet

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder, BitPackEnum
from randovania.game_description import default_database
from randovania.game_description.area_location import AreaLocation


class StartingLocationConfiguration(BitPackEnum, Enum):
    SHIP = "ship"
    RANDOM_SAVE_STATION = "random-save-station"
    CUSTOM = "custom"


def _areas_list():
    world_list = default_database.default_prime2_game_description().world_list
    areas = [
        AreaLocation(world.world_asset_id, area.area_asset_id)
        for world in world_list.worlds
        for area in world.areas
    ]
    return list(sorted(areas))


@dataclass(frozen=True)
class StartingLocation(BitPackValue):
    locations: FrozenSet[AreaLocation]

    @classmethod
    def with_elements(cls, elements: Iterator[AreaLocation]) -> "StartingLocation":
        return cls(frozenset(sorted(elements)))

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield from bitpacking.pack_sorted_array_elements(list(sorted(self.locations)), _areas_list())

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "StartingLocation":
        return cls.with_elements(bitpacking.decode_sorted_array_elements(decoder, _areas_list()))

    @property
    def as_json(self) -> list:
        world_list = default_database.default_prime2_game_description().world_list
        return list(sorted(
            world_list.area_name(world_list.area_by_area_location(location))
            for location in self.locations
        ))

    @classmethod
    def from_json(cls, value: list) -> "StartingLocation":
        if not isinstance(value, list):
            raise ValueError("StartingLocation from_json must receive a list, got {}".format(type(value)))

        world_list = default_database.default_prime2_game_description().world_list

        elements = []
        for location in value:
            world_name, area_name = location.split("/")
            world = world_list.world_with_name(world_name)
            area = world.area_by_name(area_name)
            elements.append(AreaLocation(world.world_asset_id, area.area_asset_id))

        return cls.with_elements(elements)

    # @property
    # def locations(self) -> List[AreaLocation]:
    #     game = default_database.default_prime2_game_description()
    #
    #     if self.configuration == StartingLocationConfiguration.SHIP:
    #         return [game.starting_location]
    #
    #     elif self.configuration == StartingLocationConfiguration.CUSTOM:
    #         return [self.custom_location]
    #
    #     elif self.configuration == StartingLocationConfiguration.RANDOM_SAVE_STATION:
    #         return [game.world_list.node_to_area_location(node)
    #                 for node in game.world_list.all_nodes if node.name == "Save Station"]
    #     else:
    #         raise ValueError("Invalid configuration for StartLocation {}".format(self))

    def ensure_has_location(self, area_location: AreaLocation, enabled: bool) -> "StartingLocation":
        new_locations = set(self.locations)
        if enabled:
            new_locations.add(area_location)
        elif area_location in new_locations:
            new_locations.remove(area_location)

        return StartingLocation.with_elements(iter(new_locations))
