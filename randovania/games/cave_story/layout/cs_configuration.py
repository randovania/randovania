from __future__ import annotations

import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.lib import enum_lib


class CSObjective(BitPackEnum, Enum):
    long_name: str
    script: str

    BAD_ENDING = 0
    NORMAL_ENDING = 1
    BEST_ENDING = 2
    ALL_BOSSES = 3
    HUNDRED_PERCENT = 4

    @property
    def enters_hell(self) -> bool:
        return self.value >= CSObjective.BEST_ENDING.value


enum_lib.add_long_name(
    CSObjective,
    {
        CSObjective.BAD_ENDING: "Bad Ending",
        CSObjective.NORMAL_ENDING: "Normal Ending",
        CSObjective.BEST_ENDING: "Best Ending",
        CSObjective.ALL_BOSSES: "All Bosses",
        CSObjective.HUNDRED_PERCENT: "100% Completion",
    },
)

enum_lib.add_per_enum_field(
    CSObjective,
    "script",
    {
        CSObjective.BAD_ENDING: "<FL+6003",
        CSObjective.NORMAL_ENDING: "<FL+6000",
        CSObjective.BEST_ENDING: "<FL+6001",
        CSObjective.ALL_BOSSES: "<FL+6002<IT+0005",
        CSObjective.HUNDRED_PERCENT: "<FL+6004<IT+0005",
    },
)


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
