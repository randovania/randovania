import pytest

from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches


def test_invalid_tuple_sizes():
    with pytest.raises(ValueError):
        PrimeCosmeticPatches(hud_color=(0, 0, 0, 0))
    with pytest.raises(ValueError):
        PrimeCosmeticPatches(suit_color_rotations=(0, 0, 0))


def test_valid_construction():
    PrimeCosmeticPatches(hud_color=(0, 0, 0), suit_color_rotations=(0, 0, 0, 0))
