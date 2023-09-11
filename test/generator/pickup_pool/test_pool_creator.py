from __future__ import annotations

import dataclasses

from randovania.game_description.resources.location_category import LocationCategory
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.generator.pickup_pool import pool_creator
from randovania.generator.pickup_pool.pool_creator import PoolCount


def test_calculate_pool_item_count(default_echoes_configuration):
    layout_configuration = dataclasses.replace(
        default_echoes_configuration,
        standard_pickup_configuration=dataclasses.replace(
            default_echoes_configuration.standard_pickup_configuration,
            minimum_random_starting_pickups=2,
        ),
        sky_temple_keys=LayoutSkyTempleKeyMode.ALL_BOSSES,
    )

    # Run
    result = pool_creator.calculate_pool_pickup_count(layout_configuration)

    # Assert
    assert result == {
        LocationCategory.MINOR: (61, 61),
        LocationCategory.MAJOR: (57, 58),
        "Starting": (0, 2),
    }


def test_get_total_pickup_count():
    result = pool_creator.get_total_pickup_count(
        {
            LocationCategory.MAJOR: PoolCount(2, 5),
            LocationCategory.MINOR: PoolCount(7, 6),
            "Starting": PoolCount(0, 3),
        }
    )

    assert result == (9, 14)
