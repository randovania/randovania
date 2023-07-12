from __future__ import annotations

import pytest

from randovania.games.am2r.generator.pool_creator import artifact_pool, create_am2r_artifact
from randovania.games.am2r.layout.am2r_configuration import AM2RArtifactConfig
from randovania.generator.pickup_pool import PoolResults
from randovania.layout.exceptions import InvalidConfiguration


@pytest.mark.parametrize("dna_count", [0, 1, 30, 46])
def test_am2r_pool_creator(am2r_game_description, dna_count):
    db = am2r_game_description.resource_database
    # Run
    results = artifact_pool(am2r_game_description, AM2RArtifactConfig(True, True, dna_count))

    # Assert
    assert results == PoolResults(
        [create_am2r_artifact(i, db) for i in range(dna_count)],
        {},
        [create_am2r_artifact(i, db) for i in range(dna_count, 46)]
    )


@pytest.mark.parametrize(("metroids", "bosses", "artifacts"), [
    (False, False, 1), (False, True, 7), (True, False, 47), (True, True, 47)
])
def test_am2r_artifact_pool_should_throw_on_invalid_config(am2r_game_description,
                                                           metroids, bosses, artifacts):
    # Setup
    configuration = AM2RArtifactConfig(prefer_metroids=metroids, prefer_bosses=bosses, required_artifacts=artifacts)

    # Run
    with pytest.raises(InvalidConfiguration, match="More Metroid DNA than allowed!"):
        artifact_pool(am2r_game_description, configuration)
