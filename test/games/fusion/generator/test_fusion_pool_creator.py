from __future__ import annotations

import pytest

from randovania.games.fusion.generator.pool_creator import artifact_pool, create_fusion_artifact
from randovania.games.fusion.layout.fusion_configuration import FusionArtifactConfig
from randovania.generator.pickup_pool import PoolResults
from randovania.layout.exceptions import InvalidConfiguration


@pytest.mark.parametrize("metroid_count", [0, 1, 11, 20])
def test_fusion_pool_creator(fusion_game_description, metroid_count):
    db = fusion_game_description.resource_database
    # Run
    results = artifact_pool(fusion_game_description, FusionArtifactConfig(True, True, metroid_count))

    # Assert
    assert results == PoolResults(
        [create_fusion_artifact(i, db) for i in range(metroid_count)],
        {},
        [create_fusion_artifact(i, db) for i in range(metroid_count, 20)],
    )


@pytest.mark.parametrize(
    ("bosses", "anywhere", "artifacts"),
    [
        (False, False, 1),
        (True, False, 12),
        (True, True, 21),
        (False, True, 21),
    ],
)
def test_fusion_artifact_pool_should_throw_on_invalid_config(fusion_game_description, bosses, anywhere, artifacts):
    # Setup
    configuration = FusionArtifactConfig(prefer_bosses=bosses, prefer_anywhere=anywhere, required_artifacts=artifacts)

    # Run
    with pytest.raises(InvalidConfiguration, match="More Infant Metroids than allowed!"):
        artifact_pool(fusion_game_description, configuration)
