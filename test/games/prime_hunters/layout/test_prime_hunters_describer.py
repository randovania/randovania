from __future__ import annotations

import dataclasses

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime_hunters.layout.prime_hunters_configuration import (
    HuntersConfiguration,
    HuntersOctolithConfig,
)
from randovania.interface_common.preset_manager import PresetManager


@pytest.mark.parametrize(
    ("octoliths"),
    [
        HuntersOctolithConfig(True, False, 8),
        HuntersOctolithConfig(True, False, 4),
        HuntersOctolithConfig(True, False, 0),
    ],
)
def test_hunters_format_params(octoliths) -> None:
    # Setup
    preset = PresetManager(None).default_preset_for_game(RandovaniaGame.METROID_PRIME_HUNTERS).get_preset()
    assert isinstance(preset.configuration, HuntersConfiguration)
    configuration = dataclasses.replace(
        preset.configuration,
        octoliths=octoliths,
    )

    # Run
    result = RandovaniaGame.METROID_PRIME_HUNTERS.data.layout.preset_describer.format_params(configuration)

    if octoliths.prefer_anywhere:
        octoliths_where = "Place at any item location"
    else:
        octoliths_where = "Prefers Bosses"

    # Assert
    assert dict(result) == {
        "Logic Settings": ["All tricks disabled"],
        "Pickup Pool": [f"Size: {82 + octoliths.placed_octoliths} of 90", "Unmodified starting pickup"],
        "Gameplay": [
            "Starts at Celestial Archives - Celestial Gateway",
            "Force Fields: Vanilla",
        ],
        "Difficulty": [],
        "Goal": (
            [f"{octoliths.placed_octoliths} Octoliths", octoliths_where]
            if octoliths.placed_octoliths
            else ["Defeat Gorea 1"]
        ),
        "Game Changes": [],
        "Hints": ["Octolith Hints: Region only"],
    }
