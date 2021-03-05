from dataclasses import dataclass
from typing import Iterator, Tuple, FrozenSet, List

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder
from randovania.game_description import default_database
from randovania.game_description.area_location import AreaLocation
from randovania.games.game import RandovaniaGame


@dataclass(frozen=True)
class LocationList(BitPackValue):
    locations: FrozenSet[AreaLocation]
    game: RandovaniaGame

    @classmethod
    def areas_list(cls, game: RandovaniaGame):
        world_list = default_database.game_description_for(game).world_list
        areas = [
            AreaLocation(world.world_asset_id, area.area_asset_id)
            for world in world_list.worlds
            for area in world.areas
            if area.valid_starting_location
        ]
        return list(sorted(areas))

    @classmethod
    def with_elements(cls, elements: Iterator[AreaLocation], game: RandovaniaGame) -> "LocationList":
        return cls(frozenset(sorted(elements)), game)

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield from bitpacking.pack_sorted_array_elements(list(sorted(self.locations)), self.areas_list(self.game))

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "LocationList":
        game = metadata["reference"].game
        return cls.with_elements(bitpacking.decode_sorted_array_elements(decoder, cls.areas_list(game)), game)

    @property
    def as_json(self) -> List[dict]:
        return [location.as_json for location in self.locations]

    @classmethod
    def from_json(cls, value: List[dict], game: RandovaniaGame) -> "LocationList":
        if not isinstance(value, list):
            raise ValueError("StartingLocation from_json must receive a list, got {}".format(type(value)))

        elements = [AreaLocation.from_json(location) for location in value]
        return cls.with_elements(elements, game)

    def ensure_has_location(self, area_location: AreaLocation, enabled: bool) -> "LocationList":
        new_locations = set(self.locations)
        if enabled:
            new_locations.add(area_location)
        elif area_location in new_locations:
            new_locations.remove(area_location)

        return LocationList.with_elements(iter(new_locations), self.game)

    def ensure_has_locations(self, area_locations: list, enabled: bool) -> "LocationList":
        new_locations = set(self.locations)
        for area_location in area_locations:
            if enabled:
                new_locations.add(area_location)
            elif area_location in new_locations:
                new_locations.remove(area_location)
        return LocationList.with_elements(iter(new_locations), self.game)
