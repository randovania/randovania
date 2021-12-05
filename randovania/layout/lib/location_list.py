from dataclasses import dataclass
from typing import Iterator, Tuple, List, Callable, TypeVar, Type, Iterable

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder
from randovania.game_description import default_database
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.games.game import RandovaniaGame


def _sorted_area_identifiers(elements: Iterable[AreaIdentifier]) -> list[AreaIdentifier]:
    return sorted(elements)


def area_locations_with_filter(game: RandovaniaGame, condition: Callable[[Area], bool]) -> list[AreaIdentifier]:
    world_list = default_database.game_description_for(game).world_list
    identifiers = [
        AreaIdentifier(
            world_name=world.name,
            area_name=area.name,
        )
        for world in world_list.worlds
        for area in world.areas
        if condition(area)
    ]
    return _sorted_area_identifiers(identifiers)


T = TypeVar("T")
SelfType = TypeVar("SelfType")


@dataclass(frozen=True)
class LocationList(BitPackValue):
    locations: tuple[AreaIdentifier, ...]
    game: RandovaniaGame

    def __post_init__(self):
        if not isinstance(self.locations, tuple):
            raise ValueError("locations must be tuple, got {}".format(type(self.locations)))

        if list(self.locations) != sorted(self.locations):
            raise ValueError("locations aren't sorted: {}".format(self.locations))

    @classmethod
    def areas_list(cls, game: RandovaniaGame) -> List[AreaIdentifier]:
        return area_locations_with_filter(game, lambda area: True)

    @classmethod
    def element_type(cls) -> Type[AreaIdentifier]:
        return AreaIdentifier

    @classmethod
    def with_elements(cls: Type[SelfType], elements: Iterable[AreaIdentifier], game: RandovaniaGame) -> SelfType:
        elements_set = frozenset(elements)
        all_locations = frozenset(cls.areas_list(game))
        return cls(tuple(_sorted_area_identifiers(elements_set & all_locations)), game)

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        areas = self.areas_list(self.game)
        yield from bitpacking.pack_sorted_array_elements(list(self.locations), areas)

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

        elements = [cls.element_type().from_json(location) for location in value]
        return cls.with_elements(elements, game)

    def ensure_has_location(self: SelfType, area_location: AreaIdentifier, enabled: bool) -> SelfType:
        new_locations = set(self.locations)

        if enabled:
            new_locations.add(area_location)
        elif area_location in new_locations:
            new_locations.remove(area_location)

        return self.with_elements(iter(new_locations), self.game)

    def ensure_has_locations(self: SelfType, area_locations: List[AreaIdentifier], enabled: bool) -> SelfType:
        new_locations = set(self.locations)

        for area_location in area_locations:
            if enabled:
                new_locations.add(area_location)
            elif area_location in new_locations:
                new_locations.remove(area_location)

        return self.with_elements(new_locations, self.game)
