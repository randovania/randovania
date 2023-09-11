from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.game_description import default_database

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.pickup.ammo_pickup import AmmoPickupDefinition


@dataclasses.dataclass(frozen=True)
class AmmoPickupState(BitPackValue):
    ammo_count: tuple[int, ...] = (0,)
    pickup_count: int = 0
    requires_main_item: bool = True

    def check_consistency(self, ammo: AmmoPickupDefinition):
        db = default_database.resource_database_for(ammo.game)

        if len(self.ammo_count) != len(ammo.items):
            raise ValueError(f"Ammo state has {len(self.ammo_count)} ammo counts, expected {len(ammo.items)}")

        for count, ammo_name in zip(self.ammo_count, ammo.items):
            ammo_item = db.get_item(ammo_name)
            minimum_count = -ammo_item.max_capacity if ammo.allows_negative else 0
            if not (minimum_count <= count <= ammo_item.max_capacity):
                raise ValueError(
                    f"Ammo count for item {ammo_name} of value {count} is not "
                    f"in range [{minimum_count}, {ammo_item.max_capacity}]."
                )

        if self.pickup_count < 0:
            raise ValueError(f"Pickup count must be at least 0, got {self.pickup_count}")

    def bit_pack_encode(self, metadata) -> Iterator[tuple[int, int]]:
        ammo: AmmoPickupDefinition = metadata["ammo"]
        db = default_database.resource_database_for(ammo.game)

        for count, ammo_name in zip(self.ammo_count, ammo.items):
            ammo_item = db.get_item(ammo_name)
            yield from bitpacking.encode_int_with_limits(
                abs(count),
                (ammo_item.max_capacity // 2, ammo_item.max_capacity + 1),
            )
            if ammo.allows_negative:
                yield from bitpacking.encode_bool(count < 0)  # Negative?

        yield from bitpacking.encode_big_int(self.pickup_count)
        if ammo.unlocked_by is not None:
            yield from bitpacking.encode_bool(self.requires_main_item)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> AmmoPickupState:
        ammo: AmmoPickupDefinition = metadata["ammo"]
        db = default_database.resource_database_for(ammo.game)

        # Ammo Count
        ammo_count = []
        for ammo_name in ammo.items:
            ammo_item = db.get_item(ammo_name)
            count = bitpacking.decode_int_with_limits(
                decoder,
                (ammo_item.max_capacity // 2, ammo_item.max_capacity + 1),
            )
            if ammo.allows_negative and bitpacking.decode_bool(decoder):  # Negative?
                count *= -1
            ammo_count.append(count)

        # Pickup Count
        pickup_count = bitpacking.decode_big_int(decoder)

        # Require Main Item
        requires_main_item = True
        if ammo.unlocked_by is not None:
            requires_main_item = bitpacking.decode_bool(decoder)

        return cls(
            ammo_count=tuple(ammo_count),
            pickup_count=pickup_count,
            requires_main_item=requires_main_item,
        )

    @property
    def as_json(self) -> dict:
        result: dict = {}

        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            result[field.name] = value

        result["ammo_count"] = list(result["ammo_count"])

        return result

    @classmethod
    def from_json(cls, value: dict) -> AmmoPickupState:
        kwargs = {}

        for field in dataclasses.fields(cls):
            if field.name in value:
                kwargs[field.name] = value[field.name]

        if "ammo_count" in kwargs:
            kwargs["ammo_count"] = tuple(kwargs["ammo_count"])

        return cls(**kwargs)
