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
        HuntersOctolithConfig(True, 8),
        HuntersOctolithConfig(True, 4),
        HuntersOctolithConfig(True, 0),
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

    # Assert
    assert dict(result) == {
        "Logic Settings": ["All tricks disabled"],
        "Item Pool": [f"Size: {58 + octoliths.placed_octoliths} of 66", "Vanilla starting items"],
        "Gameplay": [
            "Starts at Celestial Archives - Celestial Gateway",
            "Force Fields: Vanilla",
        ],
        "Difficulty": [],
        "Goal": ([f"{octoliths.placed_octoliths} Octoliths"] if octoliths.placed_octoliths else ["Defeat Gorea 1"]),
        "Game Changes": [],
        "Hints": [],
    }
