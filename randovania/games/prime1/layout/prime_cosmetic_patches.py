import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


@dataclasses.dataclass(frozen=True)
class PrimeCosmeticPatches(BaseCosmeticPatches):
    qol_cosmetic: bool = True
    open_map: bool = True
    use_hud_color: bool = False
    hud_color: tuple[int, int, int] = (102, 174, 225)
    suit_color_rotations: tuple[int, int, int, int] = (0, 0, 0, 0)

    @classmethod
    def default(cls) -> "PrimeCosmeticPatches":
        return cls()

    @classmethod
    def game(cls):
        return RandovaniaGame.METROID_PRIME
