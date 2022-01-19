import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


class CSObjective(BitPackEnum, Enum):
    BAD_ENDING = 0
    NORMAL_ENDING = 1
    BEST_ENDING = 2
    ALL_BOSSES = 3
    HUNDRED_PERCENT = 4

    @property
    def long_name(self) -> str:
        if self == CSObjective.BAD_ENDING:
            return "Bad Ending"
        if self == CSObjective.NORMAL_ENDING:
            return "Normal Ending"
        if self == CSObjective.BEST_ENDING:
            return "Best Ending"
        if self == CSObjective.ALL_BOSSES:
            return "All Bosses"
        if self == CSObjective.HUNDRED_PERCENT:
            return "100% Completion"
        raise ValueError(f"No name for objective {self}")

    @property
    def enters_hell(self) -> bool:
        return self.value >= CSObjective.BEST_ENDING.value

    @property
    def script(self) -> str:
        if self == CSObjective.BAD_ENDING:
            return "<FL+6003"
        if self == CSObjective.NORMAL_ENDING:
            return "<FL+6000"
        if self == CSObjective.BEST_ENDING:
            return "<FL+6001"
        if self == CSObjective.ALL_BOSSES:
            return "<FL+6002<IT+0005"
        if self == CSObjective.HUNDRED_PERCENT:
            return "<FL+6004<IT+0005"
        raise ValueError(f"No script for objective {self}")


@dataclasses.dataclass(frozen=True)
class HintConfiguration(BitPackDataclass, DataclassPostInitTypeCheck, JsonDataclass):
    item_hints: bool = True


@dataclasses.dataclass(frozen=True)
class CSConfiguration(BaseConfiguration):
    puppies_anywhere: bool
    objective: CSObjective
    no_blocks: bool
    starting_hp: int = dataclasses.field(metadata={"min": 1, "max": 56, "precision": 1})
    hints: HintConfiguration = HintConfiguration()

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.CAVE_STORY
