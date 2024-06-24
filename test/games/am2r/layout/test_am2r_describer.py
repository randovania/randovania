from __future__ import annotations

import dataclasses

import pytest

from randovania.games.am2r.layout.am2r_configuration import (
    AM2RArtifactConfig,
    AM2RConfiguration,
)
from randovania.games.game import RandovaniaGame
from randovania.interface_common.preset_manager import PresetManager


@pytest.mark.parametrize(
    ("artifacts", "darkness_chance"),
    [
        (AM2RArtifactConfig(True, True, False, 5, 5), 0),
        (AM2RArtifactConfig(True, False, False, 46, 46), 50),
        (AM2RArtifactConfig(False, True, False, 3, 6), 1000),
        (AM2RArtifactConfig(False, False, False, 0, 0), 500),
        (AM2RArtifactConfig(False, False, True, 2, 5), 0),
        (AM2RArtifactConfig(False, True, True, 10, 10), 0),
        (AM2RArtifactConfig(True, False, True, 30, 40), 0),
    ],
)
def test_am2r_format_params(artifacts: AM2RArtifactConfig, darkness_chance: int) -> None:
    # Setup
    preset = PresetManager(None).default_preset_for_game(RandovaniaGame.AM2R).get_preset()
    assert isinstance(preset.configuration, AM2RConfiguration)
    configuration = dataclasses.replace(
        preset.configuration,
        artifacts=artifacts,
        darkness_chance=darkness_chance,
    )

    # Run
    result = RandovaniaGame.AM2R.data.layout.preset_describer.format_params(configuration)

    if artifacts.prefer_anywhere:
        dna_where = "Place anywhere"
    elif artifacts.prefer_metroids and artifacts.prefer_bosses:
        dna_where = "Prefers Metroids, Prefers major bosses"
    elif artifacts.prefer_metroids:
        dna_where = "Prefers Metroids"
    elif artifacts.prefer_bosses:
        dna_where = "Prefers major bosses"
    else:
        dna_where = "Kill the Queen"

    game_changes = [
        "Missiles need Launcher, Super Missiles need Launcher, Power Bombs need Launcher",
        "Enable Septoggs, Add new Nest Pipes, Softlock block checks, Screw blocks near Pipes, "
        "Industrial Complex Bomb Blocks",
        "Skip gameplay cutscenes, Open Missile Doors with Supers",
    ]

    if darkness_chance != 0:
        game_changes.append(f"{darkness_chance / 10:.1f}% chance of a room being dark")

    # Assert
    assert dict(result) == {
        "Game Changes": game_changes,
        "Gameplay": ["Starts at Main Caves - Landing Site"],
        "Goal": (
            [f"{artifacts.required_artifacts} Metroid DNA out of {artifacts.placed_artifacts}", dna_where]
            if artifacts.required_artifacts
            else [dna_where]
        ),
        "Hints": ["DNA Hint: Area and room", "Ice Beam Hint: Area only"],
        "Item Pool": [
            f"Size: {118+artifacts.placed_artifacts} of 134",
            "Vanilla starting items",
            "Excludes Varia Suit, Space Jump, Hi-Jump Boots, Gravity Suit",
            "Shuffles 2x Progressive Jump, 2x Progressive Suit",
        ],
        "Logic Settings": ["All tricks disabled"],
    }
