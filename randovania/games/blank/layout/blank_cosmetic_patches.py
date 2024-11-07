from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


@dataclasses.dataclass(frozen=True)
class BlankCosmeticPatches(BaseCosmeticPatches):
    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.BLANK
