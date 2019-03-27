from dataclasses import dataclass
from typing import Tuple, Iterator

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.item.item_category import ItemCategory

ENERGY_TANK_MAXIMUM_COUNT = 16
DEFAULT_MAXIMUM_SHUFFLED = (4, 10, 99)


@dataclass(frozen=True)
class MajorItemState:
    include_copy_in_original_location: bool = False
    num_shuffled_pickups: int = 0
    num_included_in_starting_items: int = 0
    included_ammo: Tuple[int, ...] = tuple()
    allowed_as_random_starting_item: bool = True

    @property
    def as_json(self) -> dict:
        return {
            "include_copy_in_original_location": self.include_copy_in_original_location,
            "num_shuffled_pickups": self.num_shuffled_pickups,
            "num_included_in_starting_items": self.num_included_in_starting_items,
            "included_ammo": list(self.included_ammo),
            "allowed_as_random_starting_item": self.allowed_as_random_starting_item,
        }

    @classmethod
    def from_json(cls, value: dict) -> "MajorItemState":
        return cls(
            include_copy_in_original_location=value["include_copy_in_original_location"],
            num_shuffled_pickups=value["num_shuffled_pickups"],
            num_included_in_starting_items=value["num_included_in_starting_items"],
            included_ammo=tuple(value["included_ammo"]),
            allowed_as_random_starting_item=value["allowed_as_random_starting_item"],
        )

    def bit_pack_encode(self, item: MajorItem) -> Iterator[Tuple[int, int]]:
        # original location
        yield int(self.include_copy_in_original_location), 2

        # num shuffled
        yield from bitpacking.encode_int_with_limits(self.num_shuffled_pickups, DEFAULT_MAXIMUM_SHUFFLED)

        # starting item
        yield self.num_included_in_starting_items, (
            ENERGY_TANK_MAXIMUM_COUNT if item.item_category == ItemCategory.ENERGY_TANK else 2)

        # ammo index
        assert len(self.included_ammo) == len(item.ammo_index)
        for ammo in self.included_ammo:
            yield ammo, 256

        # allowed_as_random_starting_item
        yield from bitpacking.encode_bool(self.allowed_as_random_starting_item)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, item: MajorItem) -> "MajorItemState":
        original = decoder.decode_single(2)

        # num shuffled
        shuffled = bitpacking.decode_int_with_limits(decoder, DEFAULT_MAXIMUM_SHUFFLED)

        # starting item
        starting = decoder.decode_single(ENERGY_TANK_MAXIMUM_COUNT if item.item_category == ItemCategory.ENERGY_TANK
                                         else 2)

        if item.ammo_index:
            included_ammo = decoder.decode(*[256 for _ in item.ammo_index])
        else:
            included_ammo = []

        # allowed_as_random_starting_item
        allowed_as_random_starting_item = bitpacking.decode_bool(decoder)

        return cls(
            include_copy_in_original_location=bool(original),
            num_shuffled_pickups=shuffled,
            num_included_in_starting_items=starting,
            included_ammo=tuple(included_ammo),
            allowed_as_random_starting_item=allowed_as_random_starting_item,
        )
