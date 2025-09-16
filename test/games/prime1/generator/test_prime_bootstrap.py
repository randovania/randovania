from __future__ import annotations

import dataclasses
from random import Random

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.games.prime1.generator.bootstrap import PrimeBootstrap, is_pickup_to_pre_place
from randovania.generator.pickup_pool import pool_creator


@pytest.mark.parametrize(
    ("expected", "suits"),
    [
        (1.0, []),
        (0.9, ["Varia Suit"]),
        (0.9, ["Gravity Suit"]),
        (0.9, ["Phazon Suit"]),
        (0.8, ["Varia Suit", "Phazon Suit"]),
        (0.8, ["Varia Suit", "Gravity Suit"]),
        (0.8, ["Gravity Suit", "Phazon Suit"]),
        (0.5, ["Varia Suit", "Gravity Suit", "Phazon Suit"]),
    ],
)
def test_prime1_progressive_damage_reduction(prime_game_description, expected, suits):
    # Setup
    current_resources = ResourceCollection.from_dict(
        prime_game_description,
        {prime_game_description.resource_database.get_item_by_display_name(suit): 1 for suit in suits},
    )
    bootstrap = RandovaniaGame.METROID_PRIME.generator.bootstrap
    assert isinstance(bootstrap, PrimeBootstrap)

    # Run
    result = bootstrap.prime1_progressive_damage_reduction(prime_game_description.resource_database, current_resources)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    ("expected", "suits"),
    [
        (1.0, []),
        (0.9, ["Varia Suit"]),
        (0.8, ["Gravity Suit"]),
        (0.5, ["Phazon Suit"]),
        (0.5, ["Varia Suit", "Phazon Suit"]),
        (0.8, ["Varia Suit", "Gravity Suit"]),
        (0.5, ["Gravity Suit", "Phazon Suit"]),
        (0.5, ["Varia Suit", "Gravity Suit", "Phazon Suit"]),
    ],
)
def test_prime1_absolute_damage_reduction(prime_game_description, expected, suits):
    # Setup
    current_resources = ResourceCollection.from_dict(
        prime_game_description,
        {prime_game_description.resource_database.get_item_by_display_name(suit): 1 for suit in suits},
    )
    bootstrap = RandovaniaGame.METROID_PRIME.generator.bootstrap
    assert isinstance(bootstrap, PrimeBootstrap)

    # Run
    result = bootstrap.prime1_absolute_damage_reduction(prime_game_description.resource_database, current_resources)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    ("expected", "suits"),
    [
        (1.0, []),
        (0.9, ["Varia Suit"]),
        (0.9, ["Gravity Suit"]),
        (0.7, ["Phazon Suit"]),
        (0.6, ["Varia Suit", "Phazon Suit"]),
        (0.8, ["Varia Suit", "Gravity Suit"]),
        (0.6, ["Gravity Suit", "Phazon Suit"]),
        (0.5, ["Varia Suit", "Gravity Suit", "Phazon Suit"]),
    ],
)
def test_prime1_additive_damage_reduction(prime_game_description, expected, suits):
    # Setup
    current_resources = ResourceCollection.from_dict(
        prime_game_description,
        {prime_game_description.resource_database.get_item_by_display_name(suit): 1 for suit in suits},
    )
    bootstrap = RandovaniaGame.METROID_PRIME.generator.bootstrap
    assert isinstance(bootstrap, PrimeBootstrap)

    # Run
    result = bootstrap.prime1_additive_damage_reduction(prime_game_description.resource_database, current_resources)

    # Assert
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    ("pre_place_artifact", "pre_place_phazon", "expected"),
    [
        (False, False, []),
        (True, False, [35, 135, 160, 182, 224, 269]),
        (True, True, [35, 135, 160, 182, 224, 237, 269]),
        (False, True, [224]),
    ],
)
def test_assign_pool_results(
    prime_game_description, default_prime_configuration, pre_place_artifact, pre_place_phazon, expected
):
    default_prime_configuration = dataclasses.replace(
        default_prime_configuration, pre_place_artifact=pre_place_artifact
    )
    default_prime_configuration = dataclasses.replace(default_prime_configuration, pre_place_phazon=pre_place_phazon)
    patches = GamePatches.create_from_game(prime_game_description, 0, default_prime_configuration)
    pool_results = pool_creator.calculate_pool_results(default_prime_configuration, patches.game)

    # Run
    result = PrimeBootstrap().assign_pool_results(
        Random(8000),
        default_prime_configuration,
        patches,
        pool_results,
    )
    # Assert
    shuffled_pickups = [
        pickup for pickup in pool_results.to_place if is_pickup_to_pre_place(pickup, default_prime_configuration)
    ]

    assert result.starting_equipment == pool_results.starting
    assert set(result.pickup_assignment.keys()) == {PickupIndex(i) for i in expected}
    assert shuffled_pickups == []
