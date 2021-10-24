import dataclasses
from enum import Enum

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class CorruptionSuit(Enum):
    VARIA = 0
    GRAPPLE = 1
    PED = 2
    CORRUPTED_25 = 3
    CORRUPTED_50 = 4


@dataclasses.dataclass(frozen=True)
class CorruptionCosmeticPatches(BaseCosmeticPatches):
    random_door_colors: bool = False
    random_welding_colors: bool = False
    player_suit: CorruptionSuit = CorruptionSuit.VARIA

    @classmethod
    def default(cls) -> "CorruptionCosmeticPatches":
        return cls()

    @classmethod
    def game(cls):
        return RandovaniaGame.METROID_PRIME_CORRUPTION
