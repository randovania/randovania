from __future__ import annotations

import dataclasses

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.games.yokus_island_express.layout import YokuPresetDescriber


@pytest.mark.parametrize(("starting_fruit", "expected"), [(0, False), (50, True)])
def test_describe_starting_fruit(preset_manager, starting_fruit: int, expected: bool) -> None:
    preset = preset_manager.default_preset_for_game(RandovaniaGame.YOKUS_ISLAND_EXPRESS).get_preset()
    configuration = dataclasses.replace(preset.configuration, starting_fruit=starting_fruit)

    description = YokuPresetDescriber().format_params(configuration)

    lines = [line for lines in description.values() for line in lines]
    assert any("Starting fruit: 50" in line for line in lines) == expected
