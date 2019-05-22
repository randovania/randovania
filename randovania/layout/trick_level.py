import copy
import dataclasses
from enum import Enum
from typing import List, Dict, Iterator, Tuple, FrozenSet, Optional

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackValue, BitPackDecoder
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


class LayoutTrickLevel(BitPackEnum, Enum):
    NO_TRICKS = "no-tricks"
    TRIVIAL = "trivial"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    HYPERMODE = "hypermode"
    MINIMAL_RESTRICTIONS = "minimal-restrictions"

    @classmethod
    def default(cls) -> "LayoutTrickLevel":
        return cls.NO_TRICKS

    @classmethod
    def from_number(cls, number: int) -> "LayoutTrickLevel":
        return _TRICK_LEVEL_ORDER[number]

    @property
    def as_number(self) -> int:
        return _TRICK_LEVEL_ORDER.index(self)

    @property
    def long_name(self) -> str:
        return _PRETTY_TRICK_LEVEL_NAME[self]


_TRICK_LEVEL_ORDER: List[LayoutTrickLevel] = list(LayoutTrickLevel)
_PRETTY_TRICK_LEVEL_NAME = {
    LayoutTrickLevel.NO_TRICKS: "No Tricks",
    LayoutTrickLevel.TRIVIAL: "Trivial",
    LayoutTrickLevel.EASY: "Easy",
    LayoutTrickLevel.NORMAL: "Normal",
    LayoutTrickLevel.HARD: "Hard",
    LayoutTrickLevel.HYPERMODE: "Hypermode",
    LayoutTrickLevel.MINIMAL_RESTRICTIONS: "Minimal Checking",
}


@dataclasses.dataclass(frozen=True)
class TrickLevelConfiguration(BitPackValue):
    global_level: LayoutTrickLevel = dataclasses.field(default_factory=LayoutTrickLevel.default)
    specific_levels: Dict[int, LayoutTrickLevel] = dataclasses.field(default_factory=dict)

    @classmethod
    def default(cls):
        return cls()

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield from []

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        return cls()

    @property
    def as_json(self) -> dict:
        return {
            "global_level": self.global_level.value,
        }

    @classmethod
    def from_json(cls, value: dict):
        return cls(
            global_level=LayoutTrickLevel(value["global_level"]),
        )

    def has_specific_level_for_trick(self, trick: SimpleResourceInfo) -> bool:
        return trick.index in self.specific_levels

    def level_for_trick(self, trick: SimpleResourceInfo) -> LayoutTrickLevel:
        return self.specific_levels.get(trick.index, self.global_level)

    def set_level_for_trick(self, trick: SimpleResourceInfo,
                            value: Optional[LayoutTrickLevel],
                            ) -> "TrickLevelConfiguration":
        """
        Creates a new TrickLevelConfiguration with the given trick with a changed level
        :param trick:
        :param value:
        :return:
        """
        new_levels = copy.copy(self.specific_levels)

        if value is not None:
            new_levels[trick.index] = value
        elif trick.index in new_levels:
            del new_levels[trick.index]

        return dataclasses.replace(self, specific_levels=new_levels)

    @classmethod
    def all_possible_tricks(cls) -> FrozenSet[int]:
        return frozenset({
            0,  # Scan Dash
            1,  # Difficult Bomb Jump
            2,  # Slope Jump
            3,  # R Jump
            4,  # BSJ
            5,  # Roll Jump
            6,  # Underwater Dash
            7,  # Air Underwater
            8,  # Floaty
            9,  # Infinite Speed
            10,  # SA without SJ
            11,  # Wall Boost
            12,  # Jump off Enemy
            # 14,  # Controller Reset
            15,  # Instant Morph
        })
