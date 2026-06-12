from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class MZMConfiguration(BaseConfiguration):
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_ZERO_MISSION

    def active_layers(self) -> set[str]:
        result = super().active_layers()

        return result
