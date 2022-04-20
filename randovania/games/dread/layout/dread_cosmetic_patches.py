import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


@dataclasses.dataclass(frozen=True)
class DreadCosmeticPatches(BaseCosmeticPatches):
    show_boss_lifebar: bool = False
    show_enemy_life: bool = False
    show_enemy_damage: bool = False
    show_player_damage: bool = False

    @classmethod
    def default(cls) -> "DreadCosmeticPatches":
        return cls()

    @classmethod
    def game(cls):
        return RandovaniaGame.METROID_DREAD
