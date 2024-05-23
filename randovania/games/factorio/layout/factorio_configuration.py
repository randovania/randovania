from __future__ import annotations

import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class FactorioConfiguration(BaseConfiguration):
    full_tech_tree: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.FACTORIO

    def active_layers(self) -> set[str]:
        result = super().active_layers()
        if self.full_tech_tree:
            result.add("full_tree")
        return result
