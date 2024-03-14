from __future__ import annotations

import dataclasses

import pytest

from randovania.games.fusion.layout.fusion_configuration import (
    FusionArtifactConfig,
    FusionConfiguration,
)
from randovania.games.game import RandovaniaGame
from randovania.interface_common.preset_manager import PresetManager


@pytest.mark.parametrize(
    ("artifacts"),
    [
        FusionArtifactConfig(True, True, 1, 1),
        FusionArtifactConfig(True, False, 3, 5),
        FusionArtifactConfig(False, True, 12, 15),
        FusionArtifactConfig(False, False, 0, 0),
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

    if artifacts.prefer_anywhere:
        metroids_where = "Place at any item location"
    elif artifacts.prefer_bosses:
        metroids_where = "Place on major bosses"
    else:
        metroids_where = "Kill the SA-X"

    # Assert
    assert dict(result) == {
        "Game Changes": [],
        "Gameplay": ["Starts at Main Deck - Docking Bay Hangar"],
        "Goal": (
            [f"{artifacts.required_artifacts} of {artifacts.placed_artifacts} Metroids Required", metroids_where]
            if artifacts.required_artifacts
            else [metroids_where]
        ),
        "Item Pool": [f"Size: {115+artifacts.placed_artifacts} of 120", "Vanilla starting items"],
        "Logic Settings": ["All tricks disabled"],
    }
