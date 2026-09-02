from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime_hunters.layout.prime_hunters_cosmetic_suits import HuntersSuitPreferences
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


@dataclasses.dataclass(frozen=True)
class HuntersCosmeticPatches(BaseCosmeticPatches):
    shuffle_hunter_colors: bool = False
    suit_color: HuntersSuitPreferences = dataclasses.field(default_factory=HuntersSuitPreferences)

    @classmethod
    def default(cls) -> HuntersCosmeticPatches:
        return cls()

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_HUNTERS
