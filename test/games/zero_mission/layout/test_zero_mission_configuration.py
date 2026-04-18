from __future__ import annotations

from randovania.game.game_enum import RandovaniaGame
from randovania.games.zero_mission.layout.zero_mission_configuration import MZMConfiguration


def test_has_unsupported_features(preset_manager):
    preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_ZERO_MISSION).get_preset()
    assert isinstance(preset.configuration, MZMConfiguration)


def test_no_unsupported_features(preset_manager):
    preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_ZERO_MISSION).get_preset()
    assert preset.configuration.unsupported_features() == []
