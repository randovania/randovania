import dataclasses
from enum import Enum
from typing import Iterator

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder, BitPackEnum
from randovania.game_description import default_database
from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.pickup_node import PickupNode
from randovania.games.game import RandovaniaGame


def _all_indices(db: GameDescription) -> list[int]:
    return sorted(
        node.pickup_index.index
        for node in db.world_list.iterate_nodes()
        if isinstance(node, PickupNode)
    )


class RandomizationMode(BitPackEnum, Enum):
    FULL = "full"
    MAJOR_MINOR_SPLIT = "major/minor split"

    @classmethod
    def default(cls) -> "RandomizationMode":
        return cls.FULL


@dataclasses.dataclass(frozen=True)
class AvailableLocationsConfiguration(BitPackValue):
    randomization_mode: RandomizationMode
    excluded_indices: frozenset[PickupIndex]
    game: RandovaniaGame

    @property
    def _sorted_indices(self) -> list[int]:
        return list(sorted(item.index for item in self.excluded_indices))

    @property
    def as_json(self) -> dict:
        return {
            "randomization_mode": self.randomization_mode.value,
            "excluded_indices": self._sorted_indices,
        }

    @classmethod
    def from_json(cls, value: dict, game: RandovaniaGame) -> "AvailableLocationsConfiguration":
        return cls(
            randomization_mode=RandomizationMode(value["randomization_mode"]),
            excluded_indices=frozenset(PickupIndex(item) for item in value["excluded_indices"]),
            game=game,
        )

    def bit_pack_encode(self, metadata) -> Iterator[tuple[int, int]]:
        db = default_database.game_description_for(self.game)

        yield from self.randomization_mode.bit_pack_encode(metadata)
        if self.excluded_indices:
            yield from bitpacking.encode_bool(True)
            yield from bitpacking.pack_sorted_array_elements(self._sorted_indices, _all_indices(db))
        else:
            yield from bitpacking.encode_bool(False)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        game = metadata["reference"].game
        db = default_database.game_description_for(game)

        randomization_mode = RandomizationMode.bit_pack_unpack(decoder, metadata)

        if bitpacking.decode_bool(decoder):
            indices = bitpacking.decode_sorted_array_elements(decoder, _all_indices(db))
        else:
            indices = []

        return AvailableLocationsConfiguration(
            randomization_mode=randomization_mode,
            excluded_indices=frozenset(PickupIndex(item) for item in indices),
            game=game,
        )

    def ensure_index(self, index: PickupIndex, present: bool):
        excluded_indices = set(self.excluded_indices)
        if present:
            excluded_indices.add(index)
        elif index in excluded_indices:
            excluded_indices.remove(index)
        return dataclasses.replace(self, excluded_indices=frozenset(excluded_indices))
