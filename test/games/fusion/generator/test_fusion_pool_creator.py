from __future__ import annotations

import pytest

from randovania.games.fusion.generator.pool_creator import artifact_pool, create_fusion_artifact
from randovania.games.fusion.layout.fusion_configuration import FusionArtifactConfig
from randovania.generator.pickup_pool import PoolResults
from randovania.layout.exceptions import InvalidConfiguration


@pytest.mark.parametrize(
    ("required_metroids", "placed_metroids"),
    [
        (0, 0),
        (1, 1),
        (11, 11),
        (20, 20),
    ],
)
def test_fusion_pool_creator(fusion_game_description, required_metroids, placed_metroids):
    db = fusion_game_description.resource_database
    # Run
    results = artifact_pool(
        fusion_game_description, FusionArtifactConfig(True, True, required_metroids, placed_metroids)
    )

    # Assert
    assert results == PoolResults(
        [create_fusion_artifact(i, db) for i in range(required_metroids)],
        {},
        [create_fusion_artifact(i, db) for i in range(required_metroids, 20)],
    )


@pytest.mark.parametrize(
    ("bosses", "anywhere", "required_metroids", "placed_metroids"),
    [
        (False, False, 1, 1),
        (True, False, 12, 12),
        (True, True, 21, 21),
        (False, True, 21, 21),
    ],
)
def test_fusion_artifact_pool_should_throw_on_invalid_config(
    fusion_game_description, bosses, anywhere, required_metroids, placed_metroids
):
    # Setup
    configuration = FusionArtifactConfig(
        prefer_bosses=bosses,
        prefer_anywhere=anywhere,
        required_artifacts=required_metroids,
        placed_artifacts=placed_metroids,
    )

    # Run
    with pytest.raises(InvalidConfiguration, match="More Infant Metroids than allowed!"):
        artifact_pool(fusion_game_description, configuration)
