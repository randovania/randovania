from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration

MAXIMUM_STARTING_FRUIT = 600
"""The biggest wallet: 100 fruit, plus 50 for each of the 10 Wallet Upgrades."""


@dataclasses.dataclass(frozen=True)
class YokuConfiguration(BaseConfiguration):
    starting_fruit: int = dataclasses.field(metadata={"min": 0, "max": MAXIMUM_STARTING_FRUIT, "precision": 1})

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.YOKUS_ISLAND_EXPRESS
