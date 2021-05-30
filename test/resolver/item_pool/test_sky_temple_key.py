import pytest

import randovania.games.prime.echoes_items
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.generator.item_pool import sky_temple_keys, pickup_creator
from randovania.layout.prime2.echoes_configuration import LayoutSkyTempleKeyMode


def test_sky_temple_key_distribution_logic_all_bosses_valid(echoes_resource_database):
    # Run
    results = sky_temple_keys.add_sky_temple_key_distribution_logic(echoes_resource_database,
                                                                    LayoutSkyTempleKeyMode.ALL_BOSSES)
    item_pool, pickup_assignment, initial_items = results

    # Assert
    assert item_pool == []
    assert initial_items == {}
    assert list(pickup_assignment.keys()) == sky_temple_keys._GUARDIAN_INDICES + sky_temple_keys._SUB_GUARDIAN_INDICES


def test_sky_temple_key_distribution_logic_all_guardians_valid(echoes_resource_database):
    # Run
    results = sky_temple_keys.add_sky_temple_key_distribution_logic(echoes_resource_database,
                                                                    LayoutSkyTempleKeyMode.ALL_GUARDIANS)
    item_pool, pickup_assignment, initial_items = results

    # Assert
    assert item_pool == []
    assert initial_items == {
        ItemResourceInfo(randovania.games.prime.echoes_items.SKY_TEMPLE_KEY_ITEMS[i - 1],
                         f'Sky Temple Key {i}', f'TempleKey{i}', 1, None): 1
        for i in range(4, 10)
    }
    assert list(pickup_assignment.keys()) == sky_temple_keys._GUARDIAN_INDICES


@pytest.mark.parametrize("quantity", list(range(10)))
def test_sky_temple_key_distribution_logic_with_quantity(echoes_resource_database, quantity: int):
    # Run
    results = sky_temple_keys.add_sky_temple_key_distribution_logic(echoes_resource_database,
                                                                    LayoutSkyTempleKeyMode(quantity))
    item_pool, pickup_assignment, initial_items = results

    # Assert
    assert item_pool == [
        pickup_creator.create_sky_temple_key(i, echoes_resource_database)
        for i in range(quantity)
    ]
    assert pickup_assignment == {}
    assert initial_items == {
        ItemResourceInfo(randovania.games.prime.echoes_items.SKY_TEMPLE_KEY_ITEMS[i - 1],
                         f'Sky Temple Key {i}', f'TempleKey{i}', 1, None): 1
        for i in range(quantity + 1, 10)
    }
