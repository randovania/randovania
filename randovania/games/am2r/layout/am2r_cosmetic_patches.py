from __future__ import annotations

import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


@dataclasses.dataclass(frozen=True)
class AM2RCosmeticPatches(BaseCosmeticPatches):
    show_unexplored_map: bool = True
    unveiled_blocks: bool = True
    # TODO: implement settings on room names, similar to dread. requires work on patcher side to be better implemented.
    health_hud_rotation: int = 0
    etank_hud_rotation: int = 0
    dna_hud_rotation: int = 0
    # TODO: decide how to add samus palettes. will probably only get added after patcher is integrated

    @classmethod
    def default(cls) -> AM2RCosmeticPatches:
        return cls()

    @classmethod
    def game(cls):
        return RandovaniaGame.AM2R
