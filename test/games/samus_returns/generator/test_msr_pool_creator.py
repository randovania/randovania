from __future__ import annotations

import pytest

from randovania.games.samus_returns.generator.pool_creator import artifact_pool, create_msr_artifact
from randovania.games.samus_returns.layout.msr_configuration import MSRArtifactConfig
from randovania.generator.pickup_pool import PoolResults


@pytest.mark.parametrize("dna_count", [0, 1, 30, 39])
def test_msr_pool_creator(msr_game_description, dna_count):
    db = msr_game_description.resource_database
    # Run
    results = artifact_pool(msr_game_description, MSRArtifactConfig(True, True, False, dna_count))

    # Assert
    assert results == PoolResults(
        [create_msr_artifact(i, db) for i in range(dna_count)],
        {},
        [create_msr_artifact(i, db) for i in range(dna_count, 39)],
    )
