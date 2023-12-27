from __future__ import annotations

import dataclasses
import uuid
from random import Random

from randovania.games.am2r.generator.base_patches_factory import AM2RBasePatchesFactory
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.layout import filtered_database

_door_list = [
    1047,
    1751,
    1259,
    596,
    1258,
    1279,
    1280,
    1454,
    1137,
    878,
    409,
    1246,
    1248,
    1330,
    1281,
    1336,
    1331,
    1393,
    1361,
    1491,
    1257,
    1416,
    1614,
    1561,
    1720,
    1656,
    601,
]


def test_base_patches(am2r_game_description, preset_manager) -> None:
    # Setup
    game = am2r_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    assert isinstance(base_configuration, AM2RConfiguration)
    base_configuration = dataclasses.replace(base_configuration, blue_save_doors=True)
    game_description = filtered_database.game_description_for_layout(base_configuration)

    # Run
    result = AM2RBasePatchesFactory().create_base_patches(base_configuration, Random(0), game_description, False, 0)

    # Assert
    for num in _door_list:
        assert num in result.dock_connection
