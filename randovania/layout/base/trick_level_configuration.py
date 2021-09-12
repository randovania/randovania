import collections
import copy
import dataclasses
from typing import Dict, Iterator, Tuple, List

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder
from randovania.game_description import default_database
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.games.game import RandovaniaGame
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.lib.enum_lib import iterate_enum


def _all_tricks(resource_database: ResourceDatabase):
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
        resource_database = default_database.resource_database_for(self.game)

        yield from bitpacking.encode_bool(self.minimal_logic)
        if self.minimal_logic:
            return

        encodable_levels = list(LayoutTrickLevel)
        encodable_levels.remove(LayoutTrickLevel.DISABLED)

        for trick in sorted(_all_tricks(resource_database)):
            has_trick = self.has_specific_level_for_trick(trick)
            yield from bitpacking.encode_bool(has_trick)
            if has_trick:
                yield from bitpacking.pack_array_element(self.level_for_trick(trick), encodable_levels)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        game = metadata["reference"].game
        resource_database = default_database.resource_database_for(game)

        minimal_logic = bitpacking.decode_bool(decoder)
        specific_levels = {}

        if not minimal_logic:
            encodable_levels = list(LayoutTrickLevel)
            encodable_levels.remove(LayoutTrickLevel.DISABLED)

            for trick in sorted(_all_tricks(resource_database)):
                if bitpacking.decode_bool(decoder):
                    specific_levels[trick.short_name] = decoder.decode_element(encodable_levels)

        return cls(minimal_logic, specific_levels, game)

    @property
    def pretty_description(self) -> str:
        if self.minimal_logic:
            return "Minimal Logic"

        count_at_difficulties = collections.defaultdict(list)
        for trick in _all_tricks(default_database.resource_database_for(self.game)):
            count_at_difficulties[self.level_for_trick(trick)].append(trick.long_name)

        if len(count_at_difficulties) == 1:
            for level in count_at_difficulties.keys():
                if level == LayoutTrickLevel.DISABLED:
                    return "All tricks disabled"
                return f"All tricks enabled at {level.long_name}"

        def tricks_at_level(tricks: List[str]) -> str:
            if len(tricks) != 1:
                return f"{len(tricks)}"
            else:
                return tricks[0]

        descriptions = [
            f"{tricks_at_level(count_at_difficulties[level])} at {level.long_name}"
            for level in iterate_enum(LayoutTrickLevel)
            if count_at_difficulties[level]
        ]
        return "Enabled tricks: {}".format(", ".join(descriptions))

    @property
    def as_json(self) -> dict:
        specific_levels = {
            trick_short_name: level.value
            for trick_short_name, level in sorted(self.specific_levels.items())
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
