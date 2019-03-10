from dataclasses import dataclass
from typing import Tuple, Iterator

from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.item.major_item import MajorItem, MajorItemCategory


@dataclass(frozen=True)
class MajorItemState:
    include_copy_in_original_location: bool
    num_shuffled_pickups: int
    num_included_in_starting_items: int
    included_ammo: Tuple[int, ...]

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

    def bit_pack_format(self, item: MajorItem) -> Iterator[int]:
        # original location
        yield 2

        if item.item_category == MajorItemCategory.ENERGY_TANK:
            # num shuffled
            yield 16
            # starting item
            yield 16
        else:
            # num shuffled
            yield 4
            if self.num_shuffled_pickups > 2:
                yield 8

            # starting item
            yield 2

        # included_ammo
        for _ in item.ammo_index:
            yield 256

    def bit_pack_arguments(self, item: MajorItem) -> Iterator[int]:
        yield int(self.include_copy_in_original_location)

        yield self.num_shuffled_pickups

        if self.num_included_in_starting_items < 3:
            yield self.num_included_in_starting_items
        else:
            yield 3
            yield self.num_included_in_starting_items - 3
        yield from self.included_ammo

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, item: MajorItem) -> "MajorItemState":
        original = decoder.decode(2)[0]

        if item.item_category == MajorItemCategory.ENERGY_TANK:
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
