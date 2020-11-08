import collections
import copy
import dataclasses
from enum import Enum
from typing import List, Dict, Iterator, Tuple, Optional

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackEnum, BitPackValue, BitPackDecoder
from randovania.game_description import default_database
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.interface_common.enum_lib import iterate_enum


class LayoutTrickLevel(BitPackEnum, Enum):
    NO_TRICKS = "no-tricks"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    HYPERMODE = "hypermode"
    MINIMAL_LOGIC = "minimal-logic"

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
    LayoutTrickLevel.BEGINNER: "Beginner",
    LayoutTrickLevel.INTERMEDIATE: "Intermediate",
    LayoutTrickLevel.ADVANCED: "Advanced",
    LayoutTrickLevel.EXPERT: "Expert",
    LayoutTrickLevel.HYPERMODE: "Hypermode",
    LayoutTrickLevel.MINIMAL_LOGIC: "Minimal Logic",
}


def _all_tricks():
    return default_database.default_prime2_game_description().resource_database.trick


@dataclasses.dataclass(frozen=True)
class TrickLevelConfiguration(BitPackValue):
    minimal_logic: bool = False
    specific_levels: Dict[str, LayoutTrickLevel] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        for trick, level in self.specific_levels.items():
            if not isinstance(level, LayoutTrickLevel):
                raise ValueError(f"Invalid level `{level}` for trick {trick}, expected a LayoutTrickLevel")

    @classmethod
    def default(cls):
        return cls()

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield from bitpacking.encode_bool(self.minimal_logic)

        encodable_levels = list(LayoutTrickLevel)
        encodable_levels.remove(LayoutTrickLevel.NO_TRICKS)
        encodable_levels.remove(LayoutTrickLevel.MINIMAL_LOGIC)

        for trick in sorted(_all_tricks()):
            level = self.level_for_trick(trick)
            if level in encodable_levels:
                yield from bitpacking.encode_bool(True)
                yield from bitpacking.pack_array_element(level, encodable_levels)
            else:
                yield from bitpacking.encode_bool(False)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        minimal_logic = bitpacking.decode_bool(decoder)

        encodable_levels = list(LayoutTrickLevel)
        encodable_levels.remove(LayoutTrickLevel.NO_TRICKS)
        encodable_levels.remove(LayoutTrickLevel.MINIMAL_LOGIC)

        specific_levels = {}
        for trick in sorted(_all_tricks()):
            if bitpacking.decode_bool(decoder):
                specific_levels[trick.short_name] = decoder.decode_element(encodable_levels)

        return cls(minimal_logic, specific_levels)

    @property
    def pretty_description(self) -> str:
        if self.minimal_logic:
            return LayoutTrickLevel.MINIMAL_LOGIC.long_name

        difficulties = collections.defaultdict(int)
        for trick in _all_tricks():
            difficulties[self.level_for_trick(trick)] += 1

        if len(difficulties) == 1:
            for level in difficulties.keys():
                return level.long_name

        descriptions = [
            f"{difficulties[level]} at {level.long_name}"
            for level in iterate_enum(LayoutTrickLevel)
            if difficulties[level] > 0
        ]
        return ", ".join(descriptions)

    @property
    def as_json(self) -> dict:
        specific_levels = {
            str(trick): level.value
            for trick, level in self.specific_levels.items()
        }

        return {
            "minimal_logic": self.minimal_logic,
            "specific_levels": specific_levels,
        }

    @classmethod
    def from_json(cls, value: dict):
        return cls(
            minimal_logic=value["minimal_logic"],
            specific_levels={
                trick: LayoutTrickLevel(level)
                for trick, level in value["specific_levels"].items()
            },
        )

    def has_specific_level_for_trick(self, trick: TrickResourceInfo) -> bool:
        return trick.short_name in self.specific_levels

    def level_for_trick(self, trick: TrickResourceInfo) -> LayoutTrickLevel:
        return self.specific_levels.get(trick.short_name, LayoutTrickLevel.NO_TRICKS)

    def set_level_for_trick(self, trick: TrickResourceInfo,
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
            new_levels[trick.short_name] = value
        elif trick.index in new_levels:
            del new_levels[trick.short_name]

        return dataclasses.replace(self, specific_levels=new_levels)

    def dangerous_settings(self) -> List[str]:
        if self.minimal_logic:
            return ["Minimal Logic"]
        return []
