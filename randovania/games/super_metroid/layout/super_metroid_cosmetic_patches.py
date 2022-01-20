import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class MusicMode(BitPackEnum, Enum):
    VANILLA = "vanilla_music"
    RANDOMIZED = "random_music"
    OFF = "no_music"


@dataclasses.dataclass(frozen=True)
class SuperMetroidCosmeticPatches(BaseCosmeticPatches):
    music: MusicMode = MusicMode.VANILLA
    colorblind_mode: bool = False
    max_ammo_display: bool = True
    no_demo: bool = False
    aim_with_any_button: bool = True

    @classmethod
    def default(cls) -> "SuperMetroidCosmeticPatches":
        return cls()

    @classmethod
    def game(cls):
        return RandovaniaGame.SUPER_METROID
