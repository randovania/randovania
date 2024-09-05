from __future__ import annotations

import pytest

from randovania.games.samus_returns.generator.pool_creator import artifact_pool, create_msr_artifact
from randovania.games.samus_returns.layout.msr_configuration import MSRArtifactConfig
from randovania.generator.pickup_pool import PoolResults
from randovania.layout.exceptions import InvalidConfiguration


@pytest.mark.parametrize(("required_dna", "placed_dna"), [(0, 0), (1, 1), (30, 30), (39, 39)])
def test_msr_pool_creator(msr_game_description, required_dna, placed_dna):
    db = msr_game_description.resource_database
    # Run
    results = artifact_pool(msr_game_description, MSRArtifactConfig(True, True, True, True, required_dna, placed_dna))

    # Assert
    assert results == PoolResults(
        [create_msr_artifact(i, db) for i in range(required_dna)],
        {},
        [create_msr_artifact(i, db) for i in range(placed_dna, 39)],
    )


@pytest.mark.parametrize(
    ("metroids", "stronger_metroids", "bosses", "anywhere", "required_dna", "placed_dna"),
    [
        (False, False, True, False, 5, 5),
        (False, True, False, False, 15, 15),
        (True, False, True, False, 40, 40),
        (True, True, True, False, 40, 40),
        (False, False, False, True, 40, 40),
    ],
)
def test_msr_artifact_pool_should_throw_on_invalid_config(
    msr_game_description, metroids, stronger_metroids, bosses, anywhere, required_dna, placed_dna
):
    # Setup
    configuration = MSRArtifactConfig(
        prefer_metroids=metroids,
        prefer_stronger_metroids=stronger_metroids,
        prefer_bosses=bosses,
        prefer_anywhere=anywhere,
        required_artifacts=required_dna,
        placed_artifacts=placed_dna,
    )

    # Run
    with pytest.raises(InvalidConfiguration, match="More Metroid DNA than allowed!"):
        artifact_pool(msr_game_description, configuration)
