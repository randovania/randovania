from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.game_description import default_database
from randovania.game_description.db.node_identifier import NodeIdentifier

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node
    from randovania.games.game import RandovaniaGame


def _sorted_node_identifiers(elements: Iterable[NodeIdentifier]) -> list[NodeIdentifier]:
    return sorted(elements)


def node_and_area_with_filter(game: RandovaniaGame, condition: Callable[[Area, Node], bool]) -> list[NodeIdentifier]:
    region_list = default_database.game_description_for(game).region_list
    return _sorted_node_identifiers(
        node.identifier for area in region_list.all_areas for node in area.actual_nodes if condition(area, node)
    )


def node_locations_with_filter(game: RandovaniaGame, condition: Callable[[Node], bool]) -> list[NodeIdentifier]:
    region_list = default_database.game_description_for(game).region_list
    identifiers = [node.identifier for node in region_list.all_nodes if not node.is_derived_node and condition(node)]
    return _sorted_node_identifiers(identifiers)


T = TypeVar("T")
SelfType = TypeVar("SelfType")


@dataclass(frozen=True)
class LocationList(BitPackValue):
    locations: tuple[NodeIdentifier, ...]
    game: RandovaniaGame

    def __post_init__(self):
        if not isinstance(self.locations, tuple):
            raise ValueError(f"locations must be tuple, got {type(self.locations)}")

        if list(self.locations) != sorted(self.locations):
            raise ValueError(f"locations aren't sorted: {self.locations}")

    @classmethod
    def nodes_list(cls, game: RandovaniaGame) -> list[NodeIdentifier]:
        return node_locations_with_filter(game, lambda node: True)

    @classmethod
    def element_type(cls) -> type[NodeIdentifier]:
        return NodeIdentifier

    @classmethod
    def with_elements(cls: type[SelfType], elements: Iterable[NodeIdentifier], game: RandovaniaGame) -> SelfType:
        elements_set = frozenset(elements)
        all_locations = frozenset(cls.nodes_list(game))
        return cls(tuple(sorted(elements_set & all_locations)), game)

    def bit_pack_encode(self, metadata) -> Iterator[tuple[int, int]]:
        nodes = self.nodes_list(self.game)
        yield from bitpacking.pack_sorted_array_elements(list(self.locations), nodes)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> LocationList:
        game = metadata["reference"].game
        return cls.with_elements(bitpacking.decode_sorted_array_elements(decoder, cls.nodes_list(game)), game)

    @property
    def as_json(self) -> list[dict]:
        return [location.as_json for location in self.locations]

    @classmethod
    def from_json(cls, value: list[dict], game: RandovaniaGame) -> LocationList:
        if not isinstance(value, list):
            raise ValueError(f"StartingLocation from_json must receive a list, got {type(value)}")
        elements = [cls.element_type().from_json(location) for location in value]
        return cls.with_elements(elements, game)

    def ensure_has_locations(self: SelfType, node_locations: list[NodeIdentifier], enabled: bool) -> SelfType:
        new_locations = set(self.locations)

        for node_location in node_locations:
            if enabled:
                new_locations.add(node_location)
            elif node_location in new_locations:
                new_locations.remove(node_location)

        return self.with_elements(new_locations, self.game)
