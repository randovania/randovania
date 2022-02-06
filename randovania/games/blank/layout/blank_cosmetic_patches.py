import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


@dataclasses.dataclass(frozen=True)
class BlankCosmeticPatches(BaseCosmeticPatches):
    @classmethod
    def game(cls):
        return RandovaniaGame.BLANK
