import dataclasses
from typing import Tuple, Iterator

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description import default_database
from randovania.game_description.item.major_item import MajorItem

ENERGY_TANK_MAXIMUM_COUNT = 16
DEFAULT_MAXIMUM_SHUFFLED = (2, 10, 99)


@dataclasses.dataclass(frozen=True)
class MajorItemState:
    include_copy_in_original_location: bool = False
    num_shuffled_pickups: int = 0
    num_included_in_starting_items: int = 0
    included_ammo: Tuple[int, ...] = tuple()

    def check_consistency(self, item: MajorItem):
        db = default_database.resource_database_for(item.game)

        if item.required:
            if self != MajorItemState(num_included_in_starting_items=1):
                raise ValueError("Required items must be included in starting items.")

        if self.num_included_in_starting_items > 0:
            if len(item.progression) > 1:
                raise ValueError("Progressive items cannot be starting item.")

            for progression in item.progression:
                if self.num_included_in_starting_items > db.get_item(progression).max_capacity:
                    raise ValueError("More starting copies than the item's max copy.")

        if self.include_copy_in_original_location and item.original_index is None:
            raise ValueError("Custom item cannot be vanilla.")

        if len(self.included_ammo) != len(item.ammo_index):
            raise ValueError("Mismatched included_ammo array size")

        for ammo_index, ammo in zip(item.ammo_index, self.included_ammo):
            if ammo > db.get_item(ammo_index).max_capacity:
                raise ValueError(f"Including more than maximum capacity for ammo {ammo_index}")

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
            included_ammo=tuple(included_ammo),
        )
