from __future__ import annotations

import pytest

from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches


def test_invalid_tuple_sizes():
    with pytest.raises(ValueError, match=r"HUD color must be a tuple of 3 ints."):
        PrimeCosmeticPatches(hud_color=(0, 0, 0, 0))

    with pytest.raises(ValueError, match=r"Suit color rotations must be a tuple of 4 ints."):
        PrimeCosmeticPatches(suit_color_rotations=(0, 0, 0))


def test_valid_construction():
    PrimeCosmeticPatches(hud_color=(0, 0, 0), suit_color_rotations=(0, 0, 0, 0))


@pytest.mark.parametrize(
    ("force_fusion", "match_gunship_to_power_suit", "expected"),
    [
        (False, False, 120),
        (False, True, None),
        (True, False, 120),
        (True, True, 120),
    ],
)
def test_active_gunship_color_rotation(force_fusion, match_gunship_to_power_suit, expected):
    patches = PrimeCosmeticPatches(
        force_fusion=force_fusion,
        match_gunship_to_power_suit=match_gunship_to_power_suit,
        gunship_color_rotation=120,
    )

    assert patches.active_gunship_color_rotation == expected
