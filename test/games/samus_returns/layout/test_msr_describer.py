from __future__ import annotations

import dataclasses

import pytest

from randovania.games.game import RandovaniaGame
from randovania.games.samus_returns.layout.msr_configuration import (
    MSRArtifactConfig,
    MSRConfiguration,
)
from randovania.interface_common.preset_manager import PresetManager


@pytest.mark.parametrize(
    ("artifacts"),
    [
        MSRArtifactConfig(True, True, True, False, 5),
        MSRArtifactConfig(True, True, False, False, 39),
        MSRArtifactConfig(False, False, True, False, 4),
        MSRArtifactConfig(False, False, False, False, 0),
        MSRArtifactConfig(False, False, False, True, 2),
        MSRArtifactConfig(False, False, True, True, 10),
        MSRArtifactConfig(True, True, False, True, 30),
    ],
)
def test_msr_format_params(artifacts):
    # Setup
    preset = PresetManager(None).default_preset_for_game(RandovaniaGame.METROID_SAMUS_RETURNS).get_preset()
    assert isinstance(preset.configuration, MSRConfiguration)
    configuration = dataclasses.replace(
        preset.configuration,
        artifacts=artifacts,
    )

    # Run
    result = RandovaniaGame.METROID_SAMUS_RETURNS.data.layout.preset_describer.format_params(configuration)

    if artifacts.prefer_anywhere:
        dna_where = "Place at any item location"
    elif artifacts.prefer_metroids and artifacts.prefer_stronger_metroids and artifacts.prefer_bosses:
        dna_where = "Prefers Standard Metroids, Prefers Stronger Metroids, Prefers Bosses"
    elif artifacts.prefer_metroids and artifacts.prefer_stronger_metroids:
        dna_where = "Prefers Standard Metroids, Prefers Stronger Metroids"
    elif artifacts.prefer_metroids:
        dna_where = "Prefers Standard Metroids"
    elif artifacts.prefer_stronger_metroids:
        dna_where = "Prefers Stronger Metroids"
    elif artifacts.prefer_bosses:
        dna_where = "Prefers Bosses"
    else:
        dna_where = "Defeat Proteus Ridley"

    # Assert
    assert dict(result) == {
        "Logic Settings": ["All tricks disabled"],
        "Item Pool": [
            f"Size: {174+artifacts.required_artifacts} of 211",
            "Starts with Scan Pulse",
            "Progressive Beam, Progressive Suit, Progressive Jump",
            "Energy Reserve Tank, Aeion Reserve Tank, Missile Reserve Tank",
        ],
        "Gameplay": ["Starts at Surface East - Landing Site"],
        "Difficulty": [],
        "Goal": (
            [f"{artifacts.required_artifacts} Metroid DNA", dna_where] if artifacts.required_artifacts else [dna_where]
        ),
        "Game Changes": [
            "Missile needs Launcher, Super Missile needs Launcher, Power Bomb needs Launcher",
            "Charge Beam Door Buff, Beam Door Buff, Beam Burst Buff",
            "Open Area 3 Factory Interior East Shortcut",
            "Change Surface Cavern Cavity Crumble Blocks, Change Area 1 Transport to Surface and Area 2 Crumble Blocks",
        ],
        "Hints": ["Baby Metroid Hint: Area only", "DNA Hints: Area and room"],
        "Environmental Damage": [
            "Heat: Constant 20 dmg/s",
            "Lava: Constant 20 dmg/s",
        ],
    }
