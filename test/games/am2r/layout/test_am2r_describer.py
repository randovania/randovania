from __future__ import annotations

import dataclasses

import pytest

from randovania.games.am2r.layout.am2r_configuration import (
    AM2RArtifactConfig,
    AM2RConfiguration,
)
from randovania.games.game import RandovaniaGame
from randovania.interface_common.preset_manager import PresetManager


@pytest.mark.parametrize(("has_artifacts"), [(False), (True)])
def test_am2r_format_params(has_artifacts: bool):
    # Setup
    preset = PresetManager(None).default_preset_for_game(RandovaniaGame.AM2R).get_preset()
    assert isinstance(preset.configuration, AM2RConfiguration)
    configuration = dataclasses.replace(
        preset.configuration,
        artifacts=AM2RArtifactConfig(
            prefer_metroids=True,
            prefer_bosses=False,
            required_artifacts=3 if has_artifacts else 0,
        ),
    )

    # Run
    result = RandovaniaGame.AM2R.data.layout.preset_describer.format_params(configuration)

    # Assert
    assert dict(result) == {
        "Game Changes": [
            "Missiles need Launcher, Super Missiles need Launcher, Power Bombs need Launcher",
            "Enable Septoggs, Add new Nest Pipes, Softlock block checks, Screw blocks near Pipes",
            "Skip gameplay cutscenes, Open Missile Doors with Supers",
        ],
        "Gameplay": ["Starts at Main Caves - Landing Site"],
        "Goal": ["3 Metroid DNA", "Prefers Metroids"] if has_artifacts else ["Kill the Queen"],
        "Hints": ["DNA Hint: Area and room", "Ice Beam Hint: Area only"],
        "Item Pool": ["Size: 91 of 134" if has_artifacts else "Size: 88 of 134", "Vanilla starting items"],
        "Logic Settings": ["All tricks disabled"],
    }
