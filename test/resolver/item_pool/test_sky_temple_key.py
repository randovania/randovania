import pytest
from frozendict import frozendict

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.games.prime2.generator.item_pool import sky_temple_keys
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.generator.item_pool import pickup_creator

item_ids = [29, 30, 31, 101, 102, 103, 104, 105, 106]


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
        ItemResourceInfo(f'Sky Temple Key {i}', f'TempleKey{i}', 1, frozendict({"item_id": item_ids[i - 1]})): 1
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
        ItemResourceInfo(f'Sky Temple Key {i}', f'TempleKey{i}', 1, frozendict({"item_id": item_ids[i - 1]})): 1
        for i in range(quantity + 1, 10)
    }
