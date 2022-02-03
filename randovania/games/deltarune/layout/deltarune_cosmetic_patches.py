import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches

DEFAULT_HUD_COLOR = (102, 174, 225)


@dataclasses.dataclass(frozen=True)
class deltaruneCosmeticPatches(BaseCosmeticPatches):
    qol_cosmetic: bool = True
    open_map: bool = True
    use_hud_color: bool = False
    hud_color: tuple[int, int, int] = DEFAULT_HUD_COLOR
    suit_color_rotations: tuple[int, int, int, int] = (0, 0, 0, 0)

    @classmethod
    def default(cls) -> "deltaruneCosmeticPatches":
        return cls()

    @classmethod
    def game(cls):
        return RandovaniaGame.DELTARUNE

