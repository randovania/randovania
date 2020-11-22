from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Tuple, FrozenSet

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder, BitPackEnum
from randovania.game_description import default_database
from randovania.game_description.area_location import AreaLocation
from randovania.games.game import RandovaniaGame


class StartingLocationConfiguration(BitPackEnum, Enum):
    SHIP = "ship"
    RANDOM_SAVE_STATION = "random-save-station"
    CUSTOM = "custom"


def _areas_list(game: RandovaniaGame):
    world_list = default_database.game_description_for(game).world_list
    areas = [
        AreaLocation(world.world_asset_id, area.area_asset_id)
        for world in world_list.worlds
        for area in world.areas
        if area.valid_starting_location
    ]
    return list(sorted(areas))


@dataclass(frozen=True)
class StartingLocation(BitPackValue):
    locations: FrozenSet[AreaLocation]
    game: RandovaniaGame

    @classmethod
    def with_elements(cls, elements: Iterator[AreaLocation], game: RandovaniaGame) -> "StartingLocation":
        return cls(frozenset(sorted(elements)), game)

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield from bitpacking.pack_sorted_array_elements(list(sorted(self.locations)), _areas_list(self.game))

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "StartingLocation":
        game = metadata["reference"].game
        return cls.with_elements(bitpacking.decode_sorted_array_elements(decoder, _areas_list(game)), game)

    @property
    def as_json(self) -> list:
        world_list = default_database.game_description_for(self.game).world_list
        return list(sorted(
            world_list.area_name(world_list.area_by_area_location(location), separator="/",
                                 distinguish_dark_aether=False)
            for location in self.locations
        ))

    @classmethod
    def from_json(cls, value: list, game: RandovaniaGame) -> "StartingLocation":
        if not isinstance(value, list):
            raise ValueError("StartingLocation from_json must receive a list, got {}".format(type(value)))

        world_list = default_database.game_description_for(game).world_list

        elements = []
        for location in value:
            world_name, area_name = location.split("/")
            world = world_list.world_with_name(world_name)
            area = world.area_by_name(area_name)
            if area.valid_starting_location:
                elements.append(AreaLocation(world.world_asset_id, area.area_asset_id))

        return cls.with_elements(elements, game)

    def ensure_has_location(self, area_location: AreaLocation, enabled: bool) -> "StartingLocation":
        new_locations = set(self.locations)
        if enabled:
            new_locations.add(area_location)
        elif area_location in new_locations:
            new_locations.remove(area_location)

        return StartingLocation.with_elements(iter(new_locations), self.game)

    def ensure_has_locations(self, area_locations: list, enabled: bool) -> "StartingLocation":
        new_locations = set(self.locations)
        for area_location in area_locations:
            if enabled:
                new_locations.add(area_location)
            elif area_location in new_locations:
                new_locations.remove(area_location)
        return StartingLocation.with_elements(iter(new_locations), self.game)

