from dataclasses import dataclass
from typing import Iterator

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder


@dataclass(frozen=True)
class AmmoState(BitPackValue):
    variance: int
    pickup_count: int

    def bit_pack_format(self) -> Iterator[int]:
        yield 80

    def bit_pack_arguments(self) -> Iterator[int]:
        yield self.pickup_count

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder) -> "AmmoState":
        pickup_count, = decoder.decode(80)
        return cls(
            variance=0,
            pickup_count=pickup_count,
        )

    @property
    def as_json(self) -> dict:
        return {
            "variance": self.variance,
            "pickup_count": self.pickup_count,
        }

    @classmethod
    def from_json(cls, value: dict) -> "AmmoState":
        return cls(
            variance=value["variance"],
            pickup_count=value["pickup_count"],
        )
