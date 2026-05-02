from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


@dataclasses.dataclass(frozen=True)
class HuntersCosmeticPatches(BaseCosmeticPatches):
    shuffle_hunter_colors: bool = False

    @classmethod
    def default(cls) -> HuntersCosmeticPatches:
        return cls()

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_HUNTERS
