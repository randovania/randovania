from __future__ import annotations

import pytest

from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.generator.bootstrap import PrimeBootstrap


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
def test_prime1_progressive_damage_reduction(prime1_resource_database, expected, suits):
    # Setup
    current_resources = ResourceCollection.from_dict(
        prime1_resource_database, {prime1_resource_database.get_item_by_name(suit): 1 for suit in suits}
    )
    bootstrap = RandovaniaGame.METROID_PRIME.generator.bootstrap
    assert isinstance(bootstrap, PrimeBootstrap)

    # Run
    result = bootstrap.prime1_progressive_damage_reduction(prime1_resource_database, current_resources)

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
def test_prime1_absolute_damage_reduction(prime1_resource_database, expected, suits):
    # Setup
    current_resources = ResourceCollection.from_dict(
        prime1_resource_database, {prime1_resource_database.get_item_by_name(suit): 1 for suit in suits}
    )
    bootstrap = RandovaniaGame.METROID_PRIME.generator.bootstrap
    assert isinstance(bootstrap, PrimeBootstrap)

    # Run
    result = bootstrap.prime1_absolute_damage_reduction(prime1_resource_database, current_resources)

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
def test_prime1_additive_damage_reduction(prime1_resource_database, expected, suits):
    # Setup
    current_resources = ResourceCollection.from_dict(
        prime1_resource_database, {prime1_resource_database.get_item_by_name(suit): 1 for suit in suits}
    )
    bootstrap = RandovaniaGame.METROID_PRIME.generator.bootstrap
    assert isinstance(bootstrap, PrimeBootstrap)

    # Run
    result = bootstrap.prime1_additive_damage_reduction(prime1_resource_database, current_resources)

    # Assert
    assert result == pytest.approx(expected)
