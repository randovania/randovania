from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from randovania.games.cave_story.layout.cs_configuration import CSConfiguration
from randovania.games.game import RandovaniaGame
from randovania.interface_common.preset_manager import PresetManager

if TYPE_CHECKING:
    from randovania.layout.preset import Preset


@pytest.fixture(scope="session")
def default_cs_preset() -> Preset:
    return PresetManager(None).default_preset_for_game(RandovaniaGame.CAVE_STORY).get_preset()


@pytest.fixture(scope="session")
def default_cs_configuration(default_cs_preset) -> CSConfiguration:
    assert isinstance(default_cs_preset.configuration, CSConfiguration)
    return default_cs_preset.configuration
