import dataclasses
from typing import Iterator, Tuple

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder
from randovania.game_description import default_database
from randovania.game_description.item.ammo import Ammo


@dataclasses.dataclass(frozen=True)
class AmmoState(BitPackValue):
    ammo_count: Tuple[int, ...] = (0,)
    pickup_count: int = 0
    requires_major_item: bool = True

    def check_consistency(self, ammo: Ammo):
        db = default_database.resource_database_for(ammo.game)

        if len(self.ammo_count) != len(ammo.items):
            raise ValueError(f"Ammo state has {len(self.ammo_count)} ammo counts, expected {len(ammo.items)}")

        for count, ammo_index in zip(self.ammo_count, ammo.items):
            ammo_item = db.get_item(ammo_index)
            if not (0 <= count <= ammo_item.max_capacity):
                raise ValueError(f"Ammo count for item {ammo_index} of value {count} is not "
                                 f"in range [0, {ammo_item.max_capacity}].")

        if self.pickup_count < 0:
            raise ValueError(f"Pickup count must be at least 0, got {self.pickup_count}")

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        ammo: Ammo = metadata["ammo"]
        db = default_database.resource_database_for(ammo.game)

        for count, ammo_index in zip(self.ammo_count, ammo.items):
            ammo_item = db.get_item(ammo_index)
            yield from bitpacking.encode_int_with_limits(
                count,
                (ammo_item.max_capacity // 2, ammo_item.max_capacity + 1),
            )

        yield from bitpacking.encode_big_int(self.pickup_count)
        if ammo.unlocked_by is not None:
            yield from bitpacking.encode_bool(self.requires_major_item)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "AmmoState":
        ammo: Ammo = metadata["ammo"]
        db = default_database.resource_database_for(ammo.game)

        # Ammo Count
        ammo_count = []
        for ammo_index in ammo.items:
            ammo_item = db.get_item(ammo_index)
            ammo_count.append(
                bitpacking.decode_int_with_limits(
                    decoder,
                    (ammo_item.max_capacity // 2, ammo_item.max_capacity + 1),
                )
            )

        # Pickup Count
        pickup_count = bitpacking.decode_big_int(decoder)

        # Require Major Item
        requires_major_item = True
        if ammo.unlocked_by is not None:
            requires_major_item = bitpacking.decode_bool(decoder)

        return cls(
            ammo_count=tuple(ammo_count),
            pickup_count=pickup_count,
            requires_major_item=requires_major_item,
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
    def from_json(cls, value: dict) -> "AmmoState":
        kwargs = {}

        for field in dataclasses.fields(cls):
            if field.name in value:
                kwargs[field.name] = value[field.name]

        if "ammo_count" in kwargs:
            kwargs["ammo_count"] = tuple(kwargs["ammo_count"])

        return cls(**kwargs)
