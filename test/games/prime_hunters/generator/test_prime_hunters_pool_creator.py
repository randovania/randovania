from __future__ import annotations

import pytest

from randovania.games.prime_hunters.generator.pool_creator import add_alimbic_artifacts, add_octoliths
from randovania.games.prime_hunters.layout.prime_hunters_configuration import HuntersOctolithConfig
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup


@pytest.mark.parametrize("placed_octoliths", [0, 1, 4, 8])
def test_add_octoliths(prime_hunters_game_description, placed_octoliths):
    db = prime_hunters_game_description.resource_database
    pdb = prime_hunters_game_description.get_pickup_database()
    # Run
    results = add_octoliths(prime_hunters_game_description, HuntersOctolithConfig(True, placed_octoliths))

    # Assert
    assert results == PoolResults(
        [create_generated_pickup("Octolith", db, pdb, i=i + 1) for i in range(placed_octoliths)],
        {},
        [create_generated_pickup("Octolith", db, pdb, i=i + 1) for i in range(placed_octoliths, 8)],
    )


@pytest.mark.parametrize("index", range(8))
def test_create_octolith_id(index: int, prime_hunters_game_description):
    octolith = create_generated_pickup(
        "Octolith",
        prime_hunters_game_description.resource_database,
        prime_hunters_game_description.get_pickup_database(),
        i=index + 1,
    )

    assert octolith.gui_category.name == "octolith"
    assert octolith.progression == (
        (prime_hunters_game_description.resource_database.get_item(f"Octolith{index + 1}"), 1),
    )


def test_add_alimbic_artifacts(prime_hunters_game_description):
    db = prime_hunters_game_description.resource_database
    pdb = prime_hunters_game_description.get_pickup_database()
    regions = ["Celestial", "Alinos", "Arcterra", "VDO"]
    artifacts = ["Cartograph Artifact", "Attameter Artifact", "Binary Subscripture Artifact"]
    # Run
    results = add_alimbic_artifacts(db, pdb)

    # Assert
    assert results == PoolResults(
        [
            create_generated_pickup(artifact, db, pdb, i=i + 1, region=region)
            for region in regions
            for artifact in artifacts
            for i in range(2)
        ],
        {},
        [],
    )
