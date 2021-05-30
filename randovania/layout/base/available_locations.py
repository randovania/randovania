import dataclasses
from enum import Enum
from typing import Tuple, Iterator, FrozenSet, List

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder, BitPackEnum
from randovania.game_description.resources.pickup_index import PickupIndex

# FIXME: hardcoded index list
_ALL_INDICES = list(range(119))


class RandomizationMode(BitPackEnum, Enum):
    FULL = "full"
    MAJOR_MINOR_SPLIT = "major/minor split"

    @classmethod
    def default(cls) -> "RandomizationMode":
        return cls.FULL


@dataclasses.dataclass(frozen=True)
class AvailableLocationsConfiguration(BitPackValue):
    randomization_mode: RandomizationMode
    excluded_indices: FrozenSet[PickupIndex]

    @property
    def _sorted_indices(self) -> List[int]:
        return list(sorted(item.index for item in self.excluded_indices))

    @property
    def as_json(self) -> dict:
        return {
            "randomization_mode": self.randomization_mode.value,
            "excluded_indices": self._sorted_indices,
        }

    @classmethod
    def from_json(cls, value: dict) -> "AvailableLocationsConfiguration":
        return cls(
            randomization_mode=RandomizationMode(value["randomization_mode"]),
            excluded_indices=frozenset(PickupIndex(item) for item in value["excluded_indices"]),
        )

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield from self.randomization_mode.bit_pack_encode(metadata)
        if self.excluded_indices:
            yield from bitpacking.encode_bool(True)
            yield from bitpacking.pack_sorted_array_elements(self._sorted_indices, _ALL_INDICES)
        else:
            yield from bitpacking.encode_bool(False)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        randomization_mode = RandomizationMode.bit_pack_unpack(decoder, metadata)

        if bitpacking.decode_bool(decoder):
            indices = bitpacking.decode_sorted_array_elements(decoder, _ALL_INDICES)
        else:
            indices = []

        return AvailableLocationsConfiguration(
            randomization_mode=randomization_mode,
            excluded_indices=frozenset(PickupIndex(item) for item in indices),
        )

    def ensure_index(self, index: PickupIndex, present: bool):
        excluded_indices = set(self.excluded_indices)
        if present:
            excluded_indices.add(index)
        elif index in excluded_indices:
            excluded_indices.remove(index)
        return dataclasses.replace(self, excluded_indices=frozenset(excluded_indices))
