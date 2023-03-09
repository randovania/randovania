import pytest

from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.games.prime2.generator.item_pool import sky_temple_keys
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.generator.item_pool import pickup_creator

item_ids = [29, 30, 31, 101, 102, 103, 104, 105, 106]


def test_sky_temple_key_distribution_logic_all_bosses_valid(echoes_game_description):
    # Run
    results = sky_temple_keys.add_sky_temple_key_distribution_logic(echoes_game_description,
                                                                    LayoutSkyTempleKeyMode.ALL_BOSSES)

    # Assert
    assert results.pickups == []
    assert results.initial_resources == ResourceCollection.from_dict(echoes_game_description.resource_database, {})
    assert list(results.assignment.keys()) == sky_temple_keys._GUARDIAN_INDICES + sky_temple_keys._SUB_GUARDIAN_INDICES


def test_sky_temple_key_distribution_logic_all_guardians_valid(echoes_game_description):
    db = echoes_game_description.resource_database
    # Run
    results = sky_temple_keys.add_sky_temple_key_distribution_logic(echoes_game_description,
                                                                    LayoutSkyTempleKeyMode.ALL_GUARDIANS)

    # Assert
    assert results.pickups == []
    assert results.initial_resources == ResourceCollection.from_dict(db, {
        db.get_item(f'TempleKey{i}'): 1
        for i in range(4, 10)
    })
    assert list(results.assignment.keys()) == sky_temple_keys._GUARDIAN_INDICES


@pytest.mark.parametrize("quantity", list(range(10)))
def test_sky_temple_key_distribution_logic_with_quantity(echoes_game_description, quantity: int):
    db = echoes_game_description.resource_database
    # Run
    results = sky_temple_keys.add_sky_temple_key_distribution_logic(echoes_game_description,
                                                                    LayoutSkyTempleKeyMode(quantity))

    # ItemResourceInfo(f'Sky Temple Key {i}', , 1, frozendict({"item_id": item_ids[i - 1]})): 1
    # Assert
    assert results.pickups == [
        pickup_creator.create_sky_temple_key(i, db)
        for i in range(quantity)
    ]
    assert results.assignment == {}
    assert results.initial_resources == ResourceCollection.from_dict(db, {
        db.get_item(f'TempleKey{i}'): 1
        for i in range(quantity + 1, 10)
    })
