from __future__ import annotations

import dataclasses
from enum import Enum

from randovania.bitpacking.json_dataclass import JsonDataclass
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
class PaletteShuffle(JsonDataclass):
    enabled: bool
    hue_min: int = dataclasses.field(metadata={"min": 0, "max": 360, "precision": 1})
    hue_max: int = dataclasses.field(metadata={"min": 0, "max": 360, "precision": 1})


@dataclasses.dataclass(frozen=True)
class FusionCosmeticPatches(BaseCosmeticPatches):
    suit_shuffle: PaletteShuffle = PaletteShuffle(False, 0, 360)
    beam_shuffle: PaletteShuffle = PaletteShuffle(False, 0, 360)
    enemy_shuffle: PaletteShuffle = PaletteShuffle(False, 0, 360)
    tileset_shuffle: PaletteShuffle = PaletteShuffle(False, 0, 360)

    symmetric: bool = False
    color_space: ColorSpace = ColorSpace.Oklab

    @classmethod
    def default(cls) -> FusionCosmeticPatches:
        return cls()

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.FUSION
