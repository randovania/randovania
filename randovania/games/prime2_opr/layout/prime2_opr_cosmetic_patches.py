from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime2.layout.echoes_cosmetic_patches import BaseEchoesCosmeticPatches


@dataclasses.dataclass(frozen=True)
class EchoesOPRCosmeticPatches(BaseEchoesCosmeticPatches):
    @classmethod
    def default(cls) -> EchoesOPRCosmeticPatches:
        return cls()

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_ECHOES_OPR
