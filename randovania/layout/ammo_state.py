from dataclasses import dataclass
from typing import Iterator, Tuple

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder


@dataclass(frozen=True)
class AmmoState(BitPackValue):
    variance: int = 0
    pickup_count: int = 0

    @classmethod
    def maximum_pickup_count(cls) -> int:
        return 64

    def bit_pack_encode(self) -> Iterator[Tuple[int, int]]:
        yield self.pickup_count, AmmoState.maximum_pickup_count()

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder) -> "AmmoState":
        pickup_count = decoder.decode_single(cls.maximum_pickup_count())
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
