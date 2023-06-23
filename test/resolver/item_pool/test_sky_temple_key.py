from random import Random

import pytest

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.games.prime2.generator.item_pool import sky_temple_keys
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.generator.pickup_pool import pickup_creator

item_ids = [29, 30, 31, 101, 102, 103, 104, 105, 106]
_GUARDIAN_INDICES = [
    PickupIndex(43),  # Dark Suit
    PickupIndex(79),  # Dark Visor
    PickupIndex(115),  # Annihilator Beam
]
_SUB_GUARDIAN_INDICES = [
    PickupIndex(38),  # Morph Ball Bomb
    PickupIndex(37),  # Space Jump Boots
    PickupIndex(75),  # Boost Ball
    PickupIndex(86),  # Grapple Beam
    PickupIndex(102),  # Spider Ball
    PickupIndex(88),  # Main Power Bombs
]


def test_sky_temple_key_distribution_logic_all_bosses_valid(echoes_game_description):
    # Run
    results = sky_temple_keys.add_sky_temple_key_distribution_logic(echoes_game_description,
                                                                    LayoutSkyTempleKeyMode.ALL_BOSSES,
                                                                    Random(74500))

    # Assert
    assert results.to_place == []
    assert results.starting == []
    assert sorted(results.assignment.keys()) == sorted(_GUARDIAN_INDICES + _SUB_GUARDIAN_INDICES)


def test_sky_temple_key_distribution_logic_all_guardians_valid(echoes_game_description):
    db = echoes_game_description.resource_database
    # Run
    results = sky_temple_keys.add_sky_temple_key_distribution_logic(echoes_game_description,
                                                                    LayoutSkyTempleKeyMode.ALL_GUARDIANS,
                                                                    None)

    # Assert
    assert results.to_place == []
    assert results.starting == [
        pickup_creator.create_sky_temple_key(i, db)
        for i in range(3, 9)
    ]
    assert list(results.assignment.keys()) == _GUARDIAN_INDICES


@pytest.mark.parametrize("quantity", list(range(10)))
def test_sky_temple_key_distribution_logic_with_quantity(echoes_game_description, quantity: int):
    db = echoes_game_description.resource_database
    # Run
    results = sky_temple_keys.add_sky_temple_key_distribution_logic(echoes_game_description,
                                                                    LayoutSkyTempleKeyMode(quantity),
                                                                    None)

    # Assert
    assert results.to_place == [
        pickup_creator.create_sky_temple_key(i, db)
        for i in range(quantity)
    ]
    assert results.assignment == {}
    assert results.starting == [
        pickup_creator.create_sky_temple_key(i, db)
        for i in range(quantity, 9)
    ]
