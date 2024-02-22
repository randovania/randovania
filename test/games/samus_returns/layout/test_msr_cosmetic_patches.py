from __future__ import annotations

import pytest

from randovania.games.samus_returns.layout.msr_cosmetic_patches import MSRCosmeticPatches


def test_invalid_tuple_sizes():
    with pytest.raises(ValueError, match="Laser Locked color must be a tuple of 3 ints."):
        MSRCosmeticPatches(laser_locked_color=(0, 0, 0, 0))  # type: ignore

    with pytest.raises(ValueError, match="Laser Unlocked color must be a tuple of 3 ints."):
        MSRCosmeticPatches(laser_unlocked_color=(0, 0, 0, 0))  # type: ignore

    with pytest.raises(ValueError, match="Grapple Laser Locked color must be a tuple of 3 ints."):
        MSRCosmeticPatches(grapple_laser_locked_color=(0, 0, 0, 0))  # type: ignore

    with pytest.raises(ValueError, match="Grapple Laser Unlocked color must be a tuple of 3 ints."):
        MSRCosmeticPatches(grapple_laser_unlocked_color=(0, 0, 0, 0))  # type: ignore

    with pytest.raises(ValueError, match="Energy Tank color must be a tuple of 3 ints."):
        MSRCosmeticPatches(energy_tank_color=(0, 0, 0, 0))  # type: ignore

    with pytest.raises(ValueError, match="Aeion Bar color must be a tuple of 3 ints."):
        MSRCosmeticPatches(aeion_bar_color=(0, 0, 0, 0))  # type: ignore

    with pytest.raises(ValueError, match="Ammo HUD color must be a tuple of 3 ints."):
        MSRCosmeticPatches(ammo_hud_color=(0, 0, 0, 0))  # type: ignore


def test_valid_construction():
    MSRCosmeticPatches(
        laser_locked_color=(0, 0, 0),
        laser_unlocked_color=(0, 0, 0),
        grapple_laser_locked_color=(0, 0, 0),
        grapple_laser_unlocked_color=(0, 0, 0),
        energy_tank_color=(0, 0, 0),
        aeion_bar_color=(0, 0, 0),
        ammo_hud_color=(0, 0, 0),
    )
