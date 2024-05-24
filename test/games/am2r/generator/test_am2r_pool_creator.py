from __future__ import annotations

import pytest

from randovania.games.am2r.generator.pool_creator import artifact_pool, create_am2r_artifact
from randovania.games.am2r.layout.am2r_configuration import AM2RArtifactConfig
from randovania.generator.pickup_pool import PoolResults
from randovania.layout.exceptions import InvalidConfiguration


@pytest.mark.parametrize(("required_dna", "placed_dna"), [(0, 0), (1, 1), (30, 30), (46, 46)])
def test_am2r_pool_creator(am2r_game_description, required_dna, placed_dna):
    db = am2r_game_description.resource_database
    # Run
    results = artifact_pool(am2r_game_description, AM2RArtifactConfig(True, True, True, required_dna, placed_dna))

    # Assert
    assert results == PoolResults(
        [create_am2r_artifact(i, db) for i in range(required_dna)],
        {},
        [create_am2r_artifact(i, db) for i in range(required_dna, 46)],
    )


@pytest.mark.parametrize(
    ("metroids", "bosses", "anywhere", "required_dna", "placed_dna"),
    [
        (False, False, False, 1, 1),
        (False, True, False, 7, 7),
        (True, False, False, 47, 47),
        (True, True, False, 47, 47),
        (False, False, True, 47, 47),
    ],
)
def test_am2r_artifact_pool_should_throw_on_invalid_config(
    am2r_game_description, metroids, bosses, anywhere, required_dna, placed_dna
):
    # Setup
    configuration = AM2RArtifactConfig(
        prefer_metroids=metroids,
        prefer_bosses=bosses,
        prefer_anywhere=anywhere,
        required_artifacts=required_dna,
        placed_artifacts=placed_dna,
    )

    # Run
    with pytest.raises(InvalidConfiguration, match="More Metroid DNA than allowed!"):
        artifact_pool(am2r_game_description, configuration)
