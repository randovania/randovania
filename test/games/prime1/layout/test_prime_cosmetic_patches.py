from __future__ import annotations

import pytest

from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches


def test_invalid_tuple_sizes():
    with pytest.raises(ValueError, match="HUD color must be a tuple of 3 ints."):
        PrimeCosmeticPatches(hud_color=(0, 0, 0, 0))

    with pytest.raises(ValueError, match="Suit color rotations must be a tuple of 4 ints."):
        PrimeCosmeticPatches(suit_color_rotations=(0, 0, 0))


def test_valid_construction():
    PrimeCosmeticPatches(hud_color=(0, 0, 0), suit_color_rotations=(0, 0, 0, 0))
