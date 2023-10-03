from __future__ import annotations

import dataclasses

import pytest

from randovania.games.game import RandovaniaGame
from randovania.games.samus_returns.layout.msr_configuration import (
    MSRArtifactConfig,
    MSRConfiguration,
)
from randovania.interface_common.preset_manager import PresetManager


@pytest.mark.parametrize(("metroids_only"), [(False), (True)])
def test_am2r_format_params(metroids_only: bool):
    # Setup
    preset = PresetManager(None).default_preset_for_game(RandovaniaGame.METROID_SAMUS_RETURNS).get_preset()
    assert isinstance(preset.configuration, MSRConfiguration)
    configuration = dataclasses.replace(
        preset.configuration,
        artifacts=MSRArtifactConfig(
            prefer_metroids=metroids_only,
            required_artifacts=20 if metroids_only else 0,
        ),
    )

    # Run
    result = RandovaniaGame.METROID_SAMUS_RETURNS.data.layout.preset_describer.format_params(configuration)

    # Assert
    assert dict(result) == {
        "Logic Settings": ["All tricks disabled"],
        "Item Pool": [
            "Size: 191 of 211" if metroids_only else "Size: 171 of 211",
            "Starts with Scan Pulse",
            "Progressive Beam, Progressive Jump, Progressive Suit",
        ],
        "Gameplay": ["Starts at Surface - East - Landing Site"],
        "Difficulty": [],
        "Goal": ["20 Metroid DNA", "Prefers Metroids"] if metroids_only else ["Kill Ridley"],
        "Game Changes": [
            "Nerfed Power Bombs, Open Area 3 Interior East Shortcut, "
            "Remove Area Exit Path Grapple Blocks, Remove Surface Scan Pulse Crumble Blocks, "
            "Remove Area 1 Chozo Seal Crumble Blocks"
        ],
    }
