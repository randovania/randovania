import dataclasses
from typing import Iterator, Tuple

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder


@dataclasses.dataclass(frozen=True)
class AmmoState(BitPackValue):
    variance: int = 0
    pickup_count: int = 0
    requires_major_item: bool = True

    @classmethod
    def maximum_pickup_count(cls) -> int:
        return 99

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield self.pickup_count, self.maximum_pickup_count() + 1
        yield from bitpacking.encode_bool(self.requires_major_item)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "AmmoState":
        pickup_count = decoder.decode_single(cls.maximum_pickup_count() + 1)
        requires_major_item = bitpacking.decode_bool(decoder)

        return cls(
            variance=0,
            pickup_count=pickup_count,
            requires_major_item=requires_major_item,
        )

    @property
    def as_json(self) -> dict:
        result = {}

        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            result[field.name] = value

        return result

    @classmethod
    def from_json(cls, value: dict) -> "AmmoState":
        kwargs = {}

        for field in dataclasses.fields(cls):
            if field.name in value:
                kwargs[field.name] = value[field.name]

        return cls(**kwargs)
