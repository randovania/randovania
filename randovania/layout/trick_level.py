import collections
import copy
import dataclasses
from enum import Enum
from typing import List, Dict, Iterator, Tuple

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackEnum, BitPackValue, BitPackDecoder
from randovania.game_description import data_reader
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.games.game import RandovaniaGame
from randovania.games.prime import default_data
from randovania.interface_common.enum_lib import iterate_enum


class LayoutTrickLevel(BitPackEnum, Enum):
    DISABLED = "disabled"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    HYPERMODE = "hypermode"

    @classmethod
    def default(cls) -> "LayoutTrickLevel":
        return cls.DISABLED

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
    LayoutTrickLevel.DISABLED: "Disabled",
    LayoutTrickLevel.BEGINNER: "Beginner",
    LayoutTrickLevel.INTERMEDIATE: "Intermediate",
    LayoutTrickLevel.ADVANCED: "Advanced",
    LayoutTrickLevel.EXPERT: "Expert",
    LayoutTrickLevel.HYPERMODE: "Hypermode",
}


def _all_tricks(game_data: dict):
    resource_database = data_reader.read_resource_database(game_data["resource_database"])
    return resource_database.trick


@dataclasses.dataclass(frozen=True)
class TrickLevelConfiguration(BitPackValue):
    minimal_logic: bool
    specific_levels: Dict[str, LayoutTrickLevel]
    game: RandovaniaGame

    def __post_init__(self):
        for trick, level in self.specific_levels.items():
            if not isinstance(level, LayoutTrickLevel) or level == LayoutTrickLevel.DISABLED:
                raise ValueError(f"Invalid level `{level}` for trick {trick}, "
                                 f"expected a LayoutTrickLevel that isn't NO_TRICKS")

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        game_data = default_data.read_json_then_binary(self.game)[1]

        yield from bitpacking.encode_bool(self.minimal_logic)
        if self.minimal_logic:
            return

        encodable_levels = list(LayoutTrickLevel)
        encodable_levels.remove(LayoutTrickLevel.DISABLED)

        for trick in sorted(_all_tricks(game_data)):
            has_trick = self.has_specific_level_for_trick(trick)
            yield from bitpacking.encode_bool(has_trick)
            if has_trick:
                yield from bitpacking.pack_array_element(self.level_for_trick(trick), encodable_levels)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        game = metadata["reference"].game
        game_data = default_data.read_json_then_binary(game)[1]

        minimal_logic = bitpacking.decode_bool(decoder)
        specific_levels = {}

        if not minimal_logic:
            encodable_levels = list(LayoutTrickLevel)
            encodable_levels.remove(LayoutTrickLevel.DISABLED)

            for trick in sorted(_all_tricks(game_data)):
                if bitpacking.decode_bool(decoder):
                    specific_levels[trick.short_name] = decoder.decode_element(encodable_levels)

        return cls(minimal_logic, specific_levels, game)

    @property
    def pretty_description(self) -> str:
        if self.minimal_logic:
            return "Minimal Logic"

        trick_list = _all_tricks(default_data.read_json_then_binary(self.game)[1])
        difficulties = collections.defaultdict(int)
        for trick in trick_list:
            difficulties[self.level_for_trick(trick)] += 1

        if len(difficulties) == 1:
            for level in difficulties.keys():
                return f"All at {level.long_name}"

        descriptions = [
            f"{difficulties[level]} at {level.long_name}"
            for level in iterate_enum(LayoutTrickLevel)
            if difficulties[level] > 0
        ]
        return ", ".join(descriptions)

    @property
    def as_json(self) -> dict:
        specific_levels = {
            trick_short_name: level.value
            for trick_short_name, level in self.specific_levels.items()
        }

        return {
            "minimal_logic": self.minimal_logic,
            "specific_levels": {} if self.minimal_logic else specific_levels,
        }

    @classmethod
    def from_json(cls, value: dict, game: RandovaniaGame):
        minimal_logic = value["minimal_logic"]
        specific_levels = {
            trick_short_name: LayoutTrickLevel(level)
            for trick_short_name, level in value["specific_levels"].items()
            if level != LayoutTrickLevel.DISABLED.value
        }
        return cls(
            minimal_logic=minimal_logic,
            specific_levels={} if minimal_logic else specific_levels,
            game=game,
        )

    def has_specific_level_for_trick(self, trick: TrickResourceInfo) -> bool:
        return trick.short_name in self.specific_levels

    def level_for_trick(self, trick: TrickResourceInfo) -> LayoutTrickLevel:
        return self.specific_levels.get(trick.short_name, LayoutTrickLevel.DISABLED)

    def set_level_for_trick(self, trick: TrickResourceInfo, value: LayoutTrickLevel) -> "TrickLevelConfiguration":
        """
        Creates a new TrickLevelConfiguration with the given trick with a changed level
        :param trick:
        :param value:
        :return:
        """
        assert value is not None
        new_levels = copy.copy(self.specific_levels)

        if value != LayoutTrickLevel.DISABLED:
            new_levels[trick.short_name] = value
        elif trick.short_name in new_levels:
            del new_levels[trick.short_name]

        return dataclasses.replace(self, specific_levels=new_levels)

    def dangerous_settings(self) -> List[str]:
        if self.minimal_logic:
            return ["Minimal Logic"]
        return []
