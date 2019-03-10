from dataclasses import dataclass
from typing import Iterator, Tuple

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder


@dataclass(frozen=True)
class AmmoState(BitPackValue):
    variance: int
    pickup_count: int

    def bit_pack_encode(self) -> Iterator[Tuple[int, int]]:
        yield self.pickup_count, 80

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
