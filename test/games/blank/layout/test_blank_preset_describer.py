import dataclasses
from unittest.mock import MagicMock

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.games.blank.layout.blank_configuration import BlankConfiguration
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.base.available_locations import AvailableLocationsConfiguration, RandomizationMode


@pytest.mark.parametrize(
    ("excluded_indices", "expected_count"),
    [
        ([], 0),
        ([MagicMock()], 1),
        ([MagicMock(), MagicMock()], 2),
        ([MagicMock(), MagicMock(), MagicMock(), MagicMock()], 4),
    ],
)
def test_available_location_count(excluded_indices, expected_count):
    # Setup
    preset = PresetManager(None).default_preset_for_game(RandovaniaGame.BLANK).get_preset()
    assert isinstance(preset.configuration, BlankConfiguration)

    configuration = dataclasses.replace(
        preset.configuration,
        available_locations=AvailableLocationsConfiguration(
            randomization_mode=RandomizationMode.FULL, excluded_indices=excluded_indices, game=RandovaniaGame.BLANK
        ),
    )

    # Run
    result = RandovaniaGame.BLANK.data.layout.preset_describer.format_params(configuration)
    logic_settings_list = ["All tricks disabled"]
    if expected_count != 0:
        logic_settings_list.append(f"{expected_count} locations excluded")
    expected = {
        "Logic Settings": logic_settings_list,
        "Item Pool": [
            "Size: 8 of 8",
            "Vanilla starting items",
        ],
        "Gameplay": ["Starts at Intro - Starting Area"],
    }
    assert result == expected
