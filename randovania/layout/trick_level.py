import copy
import dataclasses
from enum import Enum
from typing import List, Dict, Iterator, Tuple, FrozenSet, Optional

from randovania.bitpacking import bitpacking
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

    def __post_init__(self):
        if not isinstance(self.global_level, LayoutTrickLevel):
            raise ValueError(f"Invalid global_level `{self.global_level}`, expected a LayoutTrickLevel")

        all_possible_tricks = TrickLevelConfiguration.all_possible_tricks()
        for trick, level in self.specific_levels.items():
            if trick not in all_possible_tricks:
                raise ValueError(f"Trick `{trick}` not a possible trick.")

            if not isinstance(level, LayoutTrickLevel):
                raise ValueError(f"Invalid level `{level}` for trick {trick}, expected a LayoutTrickLevel")

    @classmethod
    def default(cls):
        return cls()

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield from self.global_level.bit_pack_encode(metadata)

        encodable_levels = list(LayoutTrickLevel)
        encodable_levels.remove(LayoutTrickLevel.MINIMAL_RESTRICTIONS)

        for trick in sorted(TrickLevelConfiguration.all_possible_tricks()):
            if trick in self.specific_levels:
                yield from bitpacking.encode_bool(True)
                yield from bitpacking.pack_array_element(self.specific_levels[trick], encodable_levels)
            else:
                yield from bitpacking.encode_bool(False)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        global_level = LayoutTrickLevel.bit_pack_unpack(decoder, metadata)

        encodable_levels = list(LayoutTrickLevel)
        encodable_levels.remove(LayoutTrickLevel.MINIMAL_RESTRICTIONS)

        specific_levels = {}
        for trick in sorted(cls.all_possible_tricks()):
            if bitpacking.decode_bool(decoder):
                specific_levels[trick] = decoder.decode_element(encodable_levels)

        return cls(global_level, specific_levels)

    @property
    def as_json(self) -> dict:
        specific_levels = {
            str(trick): level.value
            for trick, level in self.specific_levels.items()
        }

        return {
            "global_level": self.global_level.value,
            "specific_levels": specific_levels,
        }

    @classmethod
    def from_json(cls, value: dict):
        return cls(
            global_level=LayoutTrickLevel(value["global_level"]),
            specific_levels={
                int(trick): LayoutTrickLevel(level)
                for trick, level in value["specific_levels"].items()
            },
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
