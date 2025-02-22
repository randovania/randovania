from __future__ import annotations

import pytest

from randovania.games.dread.generator import pool_creator
from randovania.games.dread.layout.dread_configuration import DreadArtifactConfig
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup


@pytest.mark.parametrize("count", [0, 1, 6, 11, 12])
def test_artifact_pool(dread_game_description, dread_configuration, count: int):
    db = dread_game_description.resource_database

    # Run
    results = pool_creator.artifact_pool(dread_game_description, DreadArtifactConfig(True, True, count))

    # Assert
    assert results == PoolResults(
        to_place=[create_generated_pickup("Metroid DNA", db, i=i + 1) for i in range(count)],
        assignment={},
        starting=[create_generated_pickup("Metroid DNA", db, i=i + 1) for i in range(count, 12)],
    )
