import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


@dataclasses.dataclass(frozen=True)
class AM2RCosmeticPatches(BaseCosmeticPatches):
    @classmethod
    def game(cls):
        return RandovaniaGame.AM2R
