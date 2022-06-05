from __future__ import annotations

import dataclasses
import enum
from typing import Tuple, Iterator, Optional

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description import default_database
from randovania.game_description.item.major_item import MajorItem
from randovania.lib import enum_lib

ENERGY_TANK_MAXIMUM_COUNT = 16
DEFAULT_MAXIMUM_SHUFFLED = (2, 10, 99)
PRIORITY_LIMITS = {
    "if_different": 1.0,
    "min": 0.0,
    "max": 10.0,
    "precision": 1.0,
}


class MajorItemStateCase(enum.Enum):
    MISSING = "missing"
    VANILLA = "vanilla"
    STARTING_ITEM = "starting_item"
    SHUFFLED = "shuffled"
    CUSTOM = "custom"

    @property
    def pretty_text(self):
        return _CASE_PRETTY_TEXT[self]


_CASE_PRETTY_TEXT = {
    MajorItemStateCase.MISSING: "Excluded",
    MajorItemStateCase.VANILLA: "Vanilla",
    MajorItemStateCase.STARTING_ITEM: "Starting",
    MajorItemStateCase.SHUFFLED: "Shuffled",
    MajorItemStateCase.CUSTOM: "Custom",
}


@dataclasses.dataclass(frozen=True)
class MajorItemState:
    include_copy_in_original_location: bool = False
    num_shuffled_pickups: int = 0
    num_included_in_starting_items: int = 0
    priority: float = 1.0
    included_ammo: Tuple[int, ...] = tuple()

    def check_consistency(self, item: MajorItem):
        db = default_database.resource_database_for(item.game)

        if self.num_shuffled_pickups < 0 or self.num_shuffled_pickups > DEFAULT_MAXIMUM_SHUFFLED[-1]:
            raise ValueError(f"Can only shuffle between 0 and {DEFAULT_MAXIMUM_SHUFFLED[-1]} copies,"
                             f" got {self.num_shuffled_pickups}. ({item.name})")

        if item.must_be_starting:
            if not self.num_included_in_starting_items:
                raise ValueError(f"Required items must be included in starting items. ({item.name})")

        if self.num_included_in_starting_items > 0:
            if len(item.progression) > 1:
                raise ValueError(f"Progressive items cannot be starting item. ({item.name})")

            for progression in item.progression:
                if self.num_included_in_starting_items > db.get_item(progression).max_capacity:
                    raise ValueError(f"More starting copies than the item's max copy. ({item.name})")

        if self.include_copy_in_original_location and item.original_index is None:
            raise ValueError(f"Custom item cannot be vanilla. ({item.name})")

        if not (PRIORITY_LIMITS["min"] <= self.priority <= PRIORITY_LIMITS["max"]):
            raise ValueError("Priority must be between {min} and {max}, got {priority}".format(
                priority=self.priority,
                **PRIORITY_LIMITS,
            ))

        if len(self.included_ammo) != len(item.ammo_index):
            raise ValueError(f"Mismatched included_ammo array size. ({item.name})")

        for ammo_index, ammo in zip(item.ammo_index, self.included_ammo):
            if ammo > db.get_item(ammo_index).max_capacity:
                raise ValueError(
                    f"Including more than maximum capacity for ammo {ammo_index}. Included: {ammo}; Max: {db.get_item(ammo_index).max_capacity}")

    @classmethod
    def from_case(cls, case: MajorItemStateCase, included_ammo: Tuple[int, ...]) -> Optional[MajorItemState]:
        if case == MajorItemStateCase.MISSING:
            return MajorItemState(included_ammo=included_ammo)

        elif case == MajorItemStateCase.VANILLA:
            return MajorItemState(include_copy_in_original_location=True, included_ammo=included_ammo)

        elif case == MajorItemStateCase.STARTING_ITEM:
            return MajorItemState(num_included_in_starting_items=1, included_ammo=included_ammo)

        elif case == MajorItemStateCase.SHUFFLED:
            return MajorItemState(num_shuffled_pickups=1, included_ammo=included_ammo)

        else:
            return None

    @property
    def case(self) -> MajorItemStateCase:
        for case in enum_lib.iterate_enum(MajorItemStateCase):
            if self == MajorItemState.from_case(case, self.included_ammo):
                return case

        return MajorItemStateCase.CUSTOM

    @property
    def as_json(self) -> dict:
        result: dict = {}

        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if value != field.default:
                result[field.name] = value

        if "included_ammo" in result:
            result["included_ammo"] = list(result["included_ammo"])

        return result

    @classmethod
    def from_json(cls, value: dict) -> "MajorItemState":
        kwargs: dict = {}

        for field in dataclasses.fields(cls):
            if field.name in value:
                kwargs[field.name] = value[field.name]

        if "included_ammo" in kwargs:
            kwargs["included_ammo"] = tuple(kwargs["included_ammo"])

        return cls(**kwargs)

    def bit_pack_encode(self, item: MajorItem, reference: "MajorItemState") -> Iterator[Tuple[int, int]]:
        db = default_database.resource_database_for(item.game)
        if item.progression:
            main_index = item.progression[0]
        else:
            main_index = item.ammo_index[0]
        main_item = db.get_item(main_index)

        # original location
        if item.original_index is not None:
            yield from bitpacking.encode_bool(self.include_copy_in_original_location)

        # num shuffled
        yield from bitpacking.encode_int_with_limits(self.num_shuffled_pickups, DEFAULT_MAXIMUM_SHUFFLED)

        # starting item
        if main_item.max_capacity > 1:
            yield from bitpacking.encode_int_with_limits(self.num_included_in_starting_items,
                                                         (2, main_item.max_capacity + 1))
        else:
            yield self.num_included_in_starting_items, main_item.max_capacity + 1

        # priority
        yield from bitpacking.BitPackFloat(self.priority).bit_pack_encode(PRIORITY_LIMITS)

        # ammo index
        assert len(self.included_ammo) == len(item.ammo_index)
        if self.included_ammo:
            custom_ammo = self.included_ammo != reference.included_ammo
            yield from bitpacking.encode_bool(custom_ammo)
            if custom_ammo:
                all_equal = len(set(self.included_ammo)) == 1
                if len(item.ammo_index) > 1:
                    yield from bitpacking.encode_bool(all_equal)

                for ammo_index, ammo in zip(item.ammo_index, self.included_ammo):
                    yield ammo, db.get_item(ammo_index).max_capacity + 1
                    if all_equal:
                        break

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, item: MajorItem, reference: "MajorItemState") -> "MajorItemState":
        db = default_database.resource_database_for(item.game)
        if item.progression:
            main_index = item.progression[0]
        else:
            main_index = item.ammo_index[0]
        main_item = db.get_item(main_index)

        # original location
        original = False
        if item.original_index is not None:
            original = bitpacking.decode_bool(decoder)

        # num shuffled
        shuffled = bitpacking.decode_int_with_limits(decoder, DEFAULT_MAXIMUM_SHUFFLED)

        # starting item
        if main_item.max_capacity > 1:
            starting = bitpacking.decode_int_with_limits(decoder, (2, main_item.max_capacity + 1))
        else:
            starting = decoder.decode_single(main_item.max_capacity + 1)

        # priority
        priority = bitpacking.BitPackFloat.bit_pack_unpack(decoder, PRIORITY_LIMITS)

        # ammo index
        if item.ammo_index:
            custom_ammo = bitpacking.decode_bool(decoder)
            if custom_ammo:
                all_equal = len(item.ammo_index) <= 1 or bitpacking.decode_bool(decoder)
                if all_equal:
                    ammo = decoder.decode_single(db.get_item(item.ammo_index[0]).max_capacity + 1)
                    included_ammo = [ammo] * len(item.ammo_index)
                else:
                    included_ammo = [decoder.decode_single(db.get_item(item).max_capacity + 1)
                                     for item in item.ammo_index]
            else:
                included_ammo = reference.included_ammo
        else:
            included_ammo = []

        return cls(
            include_copy_in_original_location=original,
            num_shuffled_pickups=shuffled,
            num_included_in_starting_items=starting,
            priority=priority,
            included_ammo=tuple(included_ammo),
        )
