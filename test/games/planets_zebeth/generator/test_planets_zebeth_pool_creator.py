from __future__ import annotations

import pytest

from randovania.games.planets_zebeth.generator.pool_creator import artifact_pool, create_planets_zebeth_artifact
from randovania.games.planets_zebeth.layout.planets_zebeth_configuration import PlanetsZebethArtifactConfig
from randovania.generator.pickup_pool import PoolResults
from randovania.layout.exceptions import InvalidConfiguration


@pytest.mark.parametrize("keys_count", [0, 1, 5, 9])
def test_planets_zebeth_pool_creator(planets_zebeth_game_description, keys_count):
    db = planets_zebeth_game_description.resource_database
    # Run
    results = artifact_pool(planets_zebeth_game_description, PlanetsZebethArtifactConfig(False, keys_count))

    # Assert
    assert results == PoolResults(
        [create_planets_zebeth_artifact(i, db) for i in range(keys_count)],
        {},
        [create_planets_zebeth_artifact(i, db) for i in range(keys_count, 9)],
    )


@pytest.mark.parametrize(
    ("vanilla", "artifacts"),
    [
        (False, 10),
    ],
)
def test_planets_zebeth_artifact_pool_should_throw_on_invalid_config(
    planets_zebeth_game_description, vanilla, artifacts
):
    # Setup
    configuration = PlanetsZebethArtifactConfig(vanilla_tourian_keys=vanilla, required_artifacts=artifacts)

    # Run
    with pytest.raises(InvalidConfiguration, match="More Tourian Keys than allowed!"):
        artifact_pool(planets_zebeth_game_description, configuration)
