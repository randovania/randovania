from __future__ import annotations

import dataclasses

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.games.fusion.layout.fusion_configuration import (
    FusionArtifactConfig,
    FusionConfiguration,
)
from randovania.interface_common.preset_manager import PresetManager


@pytest.mark.parametrize(
    ("artifacts"),
    [
        FusionArtifactConfig(1, 1),
        FusionArtifactConfig(3, 5),
        FusionArtifactConfig(12, 15),
        FusionArtifactConfig(0, 0),
    ],
)
def test_fusion_format_params(artifacts):
    # Setup
    preset = PresetManager(None).default_preset_for_game(RandovaniaGame.FUSION).get_preset()
    assert isinstance(preset.configuration, FusionConfiguration)
    configuration = dataclasses.replace(
        preset.configuration,
        artifacts=artifacts,
    )

    # Run
    result = RandovaniaGame.FUSION.data.layout.preset_describer.format_params(configuration)

    # Assert
    assert dict(result) == {
        "Game Changes": ["Unlocked hatches in Sector Hub"],
        "Gameplay": ["Starts at Main Deck - Sector Hub"],
        "Goal": (
            [f"{artifacts.required_artifacts} of {artifacts.placed_artifacts} Metroids Required"]
            if artifacts.required_artifacts
            else ["Kill the SA-X"]
        ),
        "Hints": ["Infant Metroids Hint: Region and area", "Charge Beam Hint: Region only"],
        "Item Pool": [
            f"Size: {121 + artifacts.placed_artifacts} of 127",
            "1 random starting items",
            "Starts with Energy Tank",
            "Shuffles 19x Energy Tank",
        ],
        "Logic Settings": ["All tricks disabled"],
    }
