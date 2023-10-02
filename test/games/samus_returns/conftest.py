from __future__ import annotations

import pytest

from randovania.games.game import RandovaniaGame
from randovania.games.samus_returns.layout import MSRConfiguration


@pytest.fixture()
def msr_configuration(preset_manager) -> MSRConfiguration:
    default_preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_SAMUS_RETURNS)
    configuration = default_preset.get_preset().configuration
    assert isinstance(configuration, MSRConfiguration)
    return configuration
