from __future__ import annotations

import dataclasses
from enum import Enum

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.lib import enum_lib


class ColorSpace(Enum):
    """Types of Color Spaces used by the palette shuffler"""

    long_name: str

    Oklab = "Oklab"
    HSV = "HSV"


enum_lib.add_long_name(
    ColorSpace,
    {
        ColorSpace.Oklab: "Oklab",
        ColorSpace.HSV: "HSV",
    },
)


@dataclasses.dataclass(frozen=True)
class FusionCosmeticPatches(BaseCosmeticPatches):
    enable_suit_palette: bool = False
    enable_beam_palette: bool = False
    enable_enemy_palette: bool = False
    enable_tileset_palette: bool = False
    color_space: ColorSpace = ColorSpace.Oklab

    @classmethod
    def default(cls) -> FusionCosmeticPatches:
        return cls()

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.FUSION
