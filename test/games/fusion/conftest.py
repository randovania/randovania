from __future__ import annotations

import pytest

from randovania.games.fusion.layout import FusionConfiguration
from randovania.games.game import RandovaniaGame


@pytest.fixture()
def fusion_configuration(preset_manager) -> FusionConfiguration:
    configuration = preset_manager.default_preset_for_game(RandovaniaGame.FUSION).get_preset().configuration
    assert isinstance(configuration, FusionConfiguration)
    return configuration
