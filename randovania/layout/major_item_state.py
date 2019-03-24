from dataclasses import dataclass
from typing import Tuple, Iterator

from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.item.item_category import ItemCategory

ENERGY_TANK_MAXIMUM_COUNT = 16
DEFAULT_MAXIMUM_SHUFFLED = 11


@dataclass(frozen=True)
class MajorItemState:
    include_copy_in_original_location: bool = False
    num_shuffled_pickups: int = 0
    num_included_in_starting_items: int = 0
    included_ammo: Tuple[int, ...] = tuple()

    @property
    def as_json(self) -> dict:
        return {
            "include_copy_in_original_location": self.include_copy_in_original_location,
            "num_shuffled_pickups": self.num_shuffled_pickups,
            "num_included_in_starting_items": self.num_included_in_starting_items,
            "included_ammo": list(self.included_ammo),
        }

    @classmethod
    def from_json(cls, value: dict) -> "MajorItemState":
        return cls(
            include_copy_in_original_location=value["include_copy_in_original_location"],
            num_shuffled_pickups=value["num_shuffled_pickups"],
            num_included_in_starting_items=value["num_included_in_starting_items"],
            included_ammo=tuple(value["included_ammo"]),
        )

    def bit_pack_encode(self, item: MajorItem) -> Iterator[Tuple[int, int]]:
        # original location
        yield int(self.include_copy_in_original_location), 2

        if item.item_category == ItemCategory.ENERGY_TANK:
            # num shuffled
            yield self.num_shuffled_pickups, ENERGY_TANK_MAXIMUM_COUNT

            # starting item
            yield self.num_included_in_starting_items, ENERGY_TANK_MAXIMUM_COUNT

        else:
            # num shuffled
            if self.num_shuffled_pickups > 2:
                yield 3, 4
                yield self.num_shuffled_pickups - 3, DEFAULT_MAXIMUM_SHUFFLED - 3
            else:
                yield self.num_shuffled_pickups, 4

            # starting item
            yield self.num_included_in_starting_items, 2

        # ammo index
        assert len(self.included_ammo) == len(item.ammo_index)
        for ammo in self.included_ammo:
            yield ammo, 256

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, item: MajorItem) -> "MajorItemState":
        original = decoder.decode(2)[0]

        if item.item_category == ItemCategory.ENERGY_TANK:
            # num shuffled
            # starting item
            shuffled, starting = decoder.decode(16, 16)
        else:
            # num shuffled
            shuffled = decoder.decode(4)[0]
            if shuffled == 3:
                shuffled = decoder.decode(8)[0] + 3

            # starting item
            starting = decoder.decode(2)[0]

        if item.ammo_index:
            included_ammo = decoder.decode(*[256 for _ in item.ammo_index])
        else:
            included_ammo = []

        return cls(
            include_copy_in_original_location=bool(original),
            num_shuffled_pickups=shuffled,
            num_included_in_starting_items=starting,
            included_ammo=tuple(included_ammo),
        )
