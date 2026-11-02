from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


@dataclasses.dataclass(frozen=True)
class YokuCosmeticPatches(BaseCosmeticPatches):
    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.YOKUS_ISLAND_EXPRESS
