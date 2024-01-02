from __future__ import annotations

import dataclasses
import uuid
from random import Random

import pytest

from randovania.game_description.db.dock import DockWeakness
from randovania.games.am2r.generator.base_patches_factory import AM2RBasePatchesFactory
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.layout import filtered_database

_save_door_list = [
    37,
    41,
    305,
    342,
    495,
    498,
    1051,
    1057,
    1058,
    1062,
    1185,
    1190,
    1191,
    1194,
    1277,
    1302,
    1303,
    1306,
    1339,
    1343,
    1345,
    1348,
    1736,
    1740,
    1741,
    1745,
    1889,
    1894,
]

_lab_door_list = [
    1764,
    1769,
    1770,
    1775,
    1776,
    1779,
    1780,
    1787,
    1788,
    1796,
    1797,
    1804,
    1805,
    1808,
]


@pytest.mark.parametrize(
    ("force_blue_saves", "force_blue_labs"),
    [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ],
)
def test_base_patches(am2r_game_description, preset_manager, force_blue_saves, force_blue_labs) -> None:
    # Setup
    game = am2r_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    assert isinstance(base_configuration, AM2RConfiguration)
    base_configuration = dataclasses.replace(
        base_configuration, blue_save_doors=force_blue_saves, force_blue_labs=force_blue_labs
    )
    game_description = filtered_database.game_description_for_layout(base_configuration)

    # Run
    result = AM2RBasePatchesFactory().create_base_patches(base_configuration, Random(0), game_description, False, 0)

    # Assert
    door_count = 0
    if force_blue_saves:
        for num in _save_door_list:
            weakness = result.dock_weakness[num]
            assert isinstance(weakness, DockWeakness)
            assert weakness.name == "Normal Door (Forced)"
            door_count += 1

    if force_blue_labs:
        for num in _lab_door_list:
            weakness = result.dock_weakness[num]
            assert isinstance(weakness, DockWeakness)
            assert weakness.name == "Normal Door (Forced)"
            door_count += 1

    get_amount_of_nones = len([door for door in result.dock_weakness if door is None])
    assert (len(result.dock_weakness) - get_amount_of_nones) == door_count
