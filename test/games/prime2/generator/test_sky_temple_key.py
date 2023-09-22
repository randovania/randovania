from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from randovania.games.prime2.generator.pickup_pool import sky_temple_keys
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.generator.pickup_pool import PoolResults

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_database import ResourceDatabase


def _create_pool_with(shuffled_count: int, db: ResourceDatabase):
    return PoolResults(
        to_place=[sky_temple_keys.create_sky_temple_key(i, db) for i in range(shuffled_count)],
        assignment={},
        starting=[sky_temple_keys.create_sky_temple_key(i, db) for i in range(shuffled_count, 9)],
    )


@pytest.mark.parametrize("index", range(9))
def test_create_key_id(index: int, echoes_resource_database):
    key = sky_temple_keys.create_sky_temple_key(index, echoes_resource_database)

    assert key.pickup_category is sky_temple_keys.SKY_TEMPLE_KEY_CATEGORY
    assert key.progression == ((echoes_resource_database.get_item(f"TempleKey{index + 1}"), 1),)


def test_sky_temple_key_distribution_logic_all_bosses_valid(echoes_game_description):
    # Run
    results = sky_temple_keys.add_sky_temple_key_distribution_logic(
        echoes_game_description, LayoutSkyTempleKeyMode.ALL_BOSSES
    )

    # Assert
    assert results == _create_pool_with(9, echoes_game_description.resource_database)


def test_sky_temple_key_distribution_logic_all_guardians_valid(echoes_game_description):
    # Run
    results = sky_temple_keys.add_sky_temple_key_distribution_logic(
        echoes_game_description, LayoutSkyTempleKeyMode.ALL_GUARDIANS
    )

    # Assert
    assert results == _create_pool_with(3, echoes_game_description.resource_database)


@pytest.mark.parametrize("quantity", list(range(10)))
def test_sky_temple_key_distribution_logic_with_quantity(echoes_game_description, quantity: int):
    # Run
    results = sky_temple_keys.add_sky_temple_key_distribution_logic(
        echoes_game_description, LayoutSkyTempleKeyMode(quantity)
    )

    # Assert
    assert results == _create_pool_with(quantity, echoes_game_description.resource_database)
