from __future__ import annotations

import dataclasses
from enum import Enum

from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.lib import enum_lib


class ColorSpace(Enum):
    """Types of Color Spaces used by the palette randomizer"""

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
    # Palette Rando
    enable_suit_palette: bool = False
    enable_suit_palette_override: bool = False
    suit_hue_min: int = 0
    suit_hue_max: int = 360
    suit_hue_override_min: int = 0
    suit_hue_override_max: int = 0
    enable_beam_palette: bool = False
    enable_beam_palette_override: bool = False
    beam_hue_min: int = 0
    beam_hue_max: int = 360
    beam_hue_override_min: int = 0
    beam_hue_override_max: int = 0
    enable_enemy_palette: bool = False
    enable_enemy_palette_override: bool = False
    enemy_hue_min: int = 0
    enemy_hue_max: int = 360
    enemy_hue_override_min: int = 0
    enemy_hue_override_max: int = 0
    enable_tileset_palette: bool = False
    enable_tileset_palette_override: bool = False
    tileset_hue_min: int = 0
    tileset_hue_max: int = 360
    tileset_hue_override_min: int = 0
    tileset_hue_override_max: int = 0
    color_space: ColorSpace = ColorSpace.Oklab
    enable_symmetric: bool = True
    # Audio Options
    stereo_default: bool = True
    disable_music: bool = False
    disable_sfx: bool = False
    # Misc Options
    starting_map: bool = True
    reveal_blocks: bool = True

    @classmethod
    def default(cls) -> FusionCosmeticPatches:
        return cls()

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.FUSION
