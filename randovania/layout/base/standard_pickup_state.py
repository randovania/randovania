from __future__ import annotations

import dataclasses
import enum
from typing import TYPE_CHECKING

from randovania.bitpacking import bitpacking
from randovania.game_description import default_database
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.bitpacking.bitpacking import BitPackDecoder
    from randovania.game_description.pickup.standard_pickup import StandardPickupDefinition

ENERGY_TANK_MAXIMUM_COUNT = 16
DEFAULT_MAXIMUM_SHUFFLED = (2, 10, 99)
PRIORITY_LIMITS = {
    "if_different": 1.0,
    "min": 0.0,
    "max": 10.0,
    "precision": 1.0,
}


class StandardPickupStateCase(enum.Enum):
    MISSING = "missing"
    VANILLA = "vanilla"
    STARTING_ITEM = "starting_item"
    SHUFFLED = "shuffled"
    CUSTOM = "custom"

    @property
    def pretty_text(self):
        return _CASE_PRETTY_TEXT[self]


_CASE_PRETTY_TEXT = {
    StandardPickupStateCase.MISSING: "Excluded",
    StandardPickupStateCase.VANILLA: "Vanilla",
    StandardPickupStateCase.STARTING_ITEM: "Starting",
    StandardPickupStateCase.SHUFFLED: "Shuffled",
    StandardPickupStateCase.CUSTOM: "Custom",
}


@dataclasses.dataclass(frozen=True)
class StandardPickupState:
    include_copy_in_original_location: bool = False
    num_shuffled_pickups: int = 0
    num_included_in_starting_pickups: int = 0
    priority: float = 1.0
    included_ammo: tuple[int, ...] = ()

    def __post_init__(self):
        for ammo in self.included_ammo:
            if not isinstance(ammo, int):
                raise ValueError(f"Expected int for ammo, got {ammo}")

    def check_consistency(self, pickup: StandardPickupDefinition):
        db = default_database.resource_database_for(pickup.game)

        if self.num_shuffled_pickups < 0 or self.num_shuffled_pickups > DEFAULT_MAXIMUM_SHUFFLED[-1]:
            raise ValueError(
                f"Can only shuffle between 0 and {DEFAULT_MAXIMUM_SHUFFLED[-1]} copies,"
                f" got {self.num_shuffled_pickups}. ({pickup.name})"
            )

        if pickup.must_be_starting:
            if not self.num_included_in_starting_pickups:
                raise ValueError(f"Required items must be included in starting items. ({pickup.name})")

        if self.num_included_in_starting_pickups > 0:
            if len(pickup.progression) > 1:
                raise ValueError(f"Progressive items cannot be starting items. ({pickup.name})")

            for progression in pickup.progression:
                if self.num_included_in_starting_pickups > db.get_item(progression).max_capacity:
                    raise ValueError(f"More starting copies than the item's maximum. ({pickup.name})")

        if self.include_copy_in_original_location and not pickup.original_locations:
            raise ValueError(f"No vanilla location defined. ({pickup.name})")

        if not (PRIORITY_LIMITS["min"] <= self.priority <= PRIORITY_LIMITS["max"]):
            raise ValueError(
                "Priority must be between {min} and {max}, got {priority}".format(
                    priority=self.priority,
                    **PRIORITY_LIMITS,
                )
            )

        if len(self.included_ammo) != len(pickup.ammo):
            raise ValueError(f"Mismatched included_ammo array size. ({pickup.name})")

        for ammo_name, ammo in zip(pickup.ammo, self.included_ammo, strict=True):
            if ammo > db.get_item(ammo_name).max_capacity:
                raise ValueError(
                    f"Including more than maximum capacity for ammo {ammo_name}."
                    f" Included: {ammo}; Max: {db.get_item(ammo_name).max_capacity}"
                )

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
    def from_json(cls, value: dict) -> StandardPickupState:
        kwargs: dict = {}

        for field in dataclasses.fields(cls):
            if field.name in value:
                kwargs[field.name] = value[field.name]

        if "included_ammo" in kwargs:
            kwargs["included_ammo"] = tuple(kwargs["included_ammo"])

        return cls(**kwargs)

    def bit_pack_encode(
        self,
        pickup: StandardPickupDefinition,
        reference: StandardPickupState,
    ) -> Iterator[tuple[int, int]]:
        db = default_database.resource_database_for(pickup.game)
        if pickup.progression:
            main_index = pickup.progression[0]
        else:
            main_index = pickup.ammo[0]
        main_item = db.get_item(main_index)

        # original location
        if pickup.original_locations:
            yield from bitpacking.encode_bool(self.include_copy_in_original_location)

        # num shuffled
        yield from bitpacking.encode_int_with_limits(self.num_shuffled_pickups, DEFAULT_MAXIMUM_SHUFFLED)

        # starting pickup
        if main_item.max_capacity > 1:
            yield from bitpacking.encode_int_with_limits(
                self.num_included_in_starting_pickups, (2, main_item.max_capacity + 1)
            )
        else:
            yield self.num_included_in_starting_pickups, main_item.max_capacity + 1

        # priority
        yield from bitpacking.BitPackFloat(self.priority).bit_pack_encode(PRIORITY_LIMITS)

        # ammo index
        assert len(self.included_ammo) == len(pickup.ammo)
        if self.included_ammo:
            custom_ammo = self.included_ammo != reference.included_ammo
            yield from bitpacking.encode_bool(custom_ammo)
            if custom_ammo:
                all_equal = len(set(self.included_ammo)) == 1
                if len(pickup.ammo) > 1:
                    yield from bitpacking.encode_bool(all_equal)

                for ammo_name, ammo in zip(pickup.ammo, self.included_ammo):
                    yield ammo, db.get_item(ammo_name).max_capacity + 1
                    if all_equal:
                        break

    @classmethod
    def bit_pack_unpack(
        cls,
        decoder: BitPackDecoder,
        pickup: StandardPickupDefinition,
        reference: StandardPickupState,
    ) -> StandardPickupState:
        db = default_database.resource_database_for(pickup.game)
        if pickup.progression:
            main_index = pickup.progression[0]
        else:
            main_index = pickup.ammo[0]
        main_item = db.get_item(main_index)

        # original location
        original = False
        if pickup.original_locations:
            original = bitpacking.decode_bool(decoder)

        # num shuffled
        shuffled = bitpacking.decode_int_with_limits(decoder, DEFAULT_MAXIMUM_SHUFFLED)

        # starting pickup
        if main_item.max_capacity > 1:
            starting = bitpacking.decode_int_with_limits(decoder, (2, main_item.max_capacity + 1))
        else:
            starting = decoder.decode_single(main_item.max_capacity + 1)

        # priority
        priority = bitpacking.BitPackFloat.bit_pack_unpack(decoder, PRIORITY_LIMITS)

        # ammo index
        if pickup.ammo:
            custom_ammo = bitpacking.decode_bool(decoder)
            if custom_ammo:
                all_equal = len(pickup.ammo) <= 1 or bitpacking.decode_bool(decoder)
                if all_equal:
                    ammo = decoder.decode_single(db.get_item(pickup.ammo[0]).max_capacity + 1)
                    included_ammo = [ammo] * len(pickup.ammo)
                else:
                    included_ammo = [decoder.decode_single(db.get_item(item).max_capacity + 1) for item in pickup.ammo]
            else:
                included_ammo = reference.included_ammo
        else:
            included_ammo = []

        return cls(
            include_copy_in_original_location=original,
            num_shuffled_pickups=shuffled,
            num_included_in_starting_pickups=starting,
            priority=priority,
            included_ammo=tuple(included_ammo),
        )

    @classmethod
    def from_case(
        cls, pickup: StandardPickupDefinition, case: StandardPickupStateCase, included_ammo: tuple[int, ...]
    ) -> StandardPickupState | None:
        if case == StandardPickupStateCase.MISSING:
            return StandardPickupState(included_ammo=included_ammo)

        elif case == StandardPickupStateCase.VANILLA:
            return StandardPickupState(include_copy_in_original_location=True, included_ammo=included_ammo)

        elif case == StandardPickupStateCase.STARTING_ITEM:
            return StandardPickupState(
                num_included_in_starting_pickups=pickup.count_for_starting_case, included_ammo=included_ammo
            )

        elif case == StandardPickupStateCase.SHUFFLED:
            return StandardPickupState(num_shuffled_pickups=pickup.count_for_shuffled_case, included_ammo=included_ammo)

        else:
            return None

    def closest_case(self, pickup: StandardPickupDefinition) -> StandardPickupStateCase:
        for case in enum_lib.iterate_enum(StandardPickupStateCase):
            if self == StandardPickupState.from_case(pickup, case, self.included_ammo):
                return case

        return StandardPickupStateCase.CUSTOM
