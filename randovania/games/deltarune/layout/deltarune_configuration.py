import dataclasses
from enum import Enum
from typing import List

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration

@dataclasses.dataclass(frozen=True)
class deltaruneConfiguration(BaseConfiguration):
    shuffle_item_pos: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.DELTARUNE

    def dangerous_settings(self) -> List[str]:
        result = super().dangerous_settings()

        if self.shuffle_item_pos:
            result.append("Shuffled item position")

        return result
