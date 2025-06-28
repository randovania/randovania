from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class PseudoregaliaConfiguration(BaseConfiguration):
    # These fields aren't necessary for a new game: they're here to have example/test features
    include_extra_pickups: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.PSEUDOREGALIA

    def active_layers(self) -> set[str]:
        result = super().active_layers()

        if self.include_extra_pickups:
            result.add("extra_pickups")

        return result
