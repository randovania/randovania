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


@pytest.mark.parametrize(
    ("required_beacons", "expected"),
    [
        (0, "Beat the final boss"),
        (1, "Light 1 beacon, then beat the final boss"),
        (5, "Light 5 beacons, then beat the final boss"),
    ],
)
def test_describe_goal(preset_manager, required_beacons: int, expected: str) -> None:
    preset = preset_manager.default_preset_for_game(RandovaniaGame.YOKUS_ISLAND_EXPRESS).get_preset()
    configuration = dataclasses.replace(preset.configuration, required_beacons=required_beacons)

    description = YokuPresetDescriber().format_params(configuration)

    assert description["Goal"] == [expected]
