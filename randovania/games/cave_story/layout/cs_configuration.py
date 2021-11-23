import dataclasses
from enum import Enum
from randovania.bitpacking.bitpacking import BitPackEnum

from randovania.game_description.requirements import Requirement
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration

class CSObjective(BitPackEnum, Enum):
    BAD_ENDING = 0
    NORMAL_ENDING = 1
    BEST_ENDING = 2
    ALL_BOSSES = 3
    HUNDRED_PERCENT = 4

    @property
    def requirements(self) -> Requirement:
        # TODO
        return Requirement.trivial
    
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

@dataclasses.dataclass(frozen=True)
class CSConfiguration(BaseConfiguration):
    puppies_anywhere: bool
    objective: CSObjective
    no_blocks: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.CAVE_STORY
