from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime2.layout.echoes_cosmetic_patches import BaseEchoesCosmeticPatches


@dataclasses.dataclass(frozen=True)
class EchoesOPRCosmeticPatches(BaseEchoesCosmeticPatches):
    reveal_all_map_icons: bool = False
    apply_hud_color_to_text: bool = True
    apply_hud_color_to_beams_visors: bool = True

    @classmethod
    def default(cls) -> EchoesOPRCosmeticPatches:
        return cls()

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_ECHOES_OPR
