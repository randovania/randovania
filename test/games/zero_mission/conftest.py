from __future__ import annotations

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.games.zero_mission.layout import MZMConfiguration


@pytest.fixture
def zero_mission_configuration(preset_manager) -> MZMConfiguration:
    configuration = (
        preset_manager.default_preset_for_game(RandovaniaGame.METROID_ZERO_MISSION).get_preset().configuration
    )
    assert isinstance(configuration, MZMConfiguration)
    return configuration
