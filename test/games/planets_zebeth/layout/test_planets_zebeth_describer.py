from __future__ import annotations

import pytest

from randovania.games.game import RandovaniaGame
from randovania.games.planets_zebeth.layout.planets_zebeth_configuration import PlanetsZebethConfiguration
from randovania.interface_common.preset_manager import PresetManager


@pytest.mark.parametrize(
    "preset_name",
    [
        "Starter Preset",
        "Starter Preset (Shuffle Keys)",
    ],
)
def test_planets_zebeth_format_params(preset_name):
    # Setup
    presets = {
        preset.name: preset.get_preset()
        for preset in PresetManager(None).presets_for_game(RandovaniaGame.METROID_PLANETS_ZEBETH)
    }
    preset = presets[preset_name]
    assert isinstance(preset.configuration, PlanetsZebethConfiguration)

    # Run
    result = RandovaniaGame.METROID_PLANETS_ZEBETH.data.layout.preset_describer.format_params(preset.configuration)

    if preset.configuration.artifacts.vanilla_tourian_keys:
        dna_where = "Kill Kraid, Ridley and Mother Brain"
    else:
        dna_where = f"{preset.configuration.artifacts.required_artifacts} Tourian Keys and kill Mother Brain"

    # Assert
    assert dict(result) == {
        "Game Changes": [],
        "Gameplay": ["Starts at Brinstar - Maru Mari Hall"],
        "Goal": [dna_where],
        "Item Pool": ["Size: 42 of 42", "Vanilla starting items"],
        "Logic Settings": ["All tricks disabled"],
    }
