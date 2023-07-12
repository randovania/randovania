from __future__ import annotations

import pytest

from randovania.games.am2r.layout import AM2RConfiguration
from randovania.games.game import RandovaniaGame


@pytest.fixture()
def am2r_configuration(preset_manager) -> AM2RConfiguration:
    configuration = preset_manager.default_preset_for_game(RandovaniaGame.AM2R).get_preset().configuration
    assert isinstance(configuration, AM2RConfiguration)
    return configuration
