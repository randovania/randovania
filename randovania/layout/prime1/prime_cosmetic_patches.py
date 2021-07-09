import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


@dataclasses.dataclass(frozen=True)
class PrimeCosmeticPatches(BaseCosmeticPatches):
    qol_cosmetic: bool = True
    open_map: bool = True

    @classmethod
    def default(cls) -> "PrimeCosmeticPatches":
        return cls()

    @classmethod
    def game(cls):
        return RandovaniaGame.METROID_PRIME
