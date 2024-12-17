from __future__ import annotations

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.games.dread.layout.dread_configuration import DreadConfiguration


@pytest.fixture
def dread_configuration(preset_manager) -> DreadConfiguration:
    configuration = preset_manager.default_preset_for_game(RandovaniaGame.METROID_DREAD).get_preset().configuration
    assert isinstance(configuration, DreadConfiguration)
    return configuration
