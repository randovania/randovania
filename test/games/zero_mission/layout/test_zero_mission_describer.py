from __future__ import annotations

from randovania.game.game_enum import RandovaniaGame
from randovania.games.zero_mission.layout.zero_mission_configuration import MZMConfiguration
from randovania.interface_common.preset_manager import PresetManager


def test_zero_mission_format_params():
    # Setup
    preset = PresetManager(None).default_preset_for_game(RandovaniaGame.METROID_ZERO_MISSION).get_preset()
    assert isinstance(preset.configuration, MZMConfiguration)

    # Run
    result = RandovaniaGame.METROID_ZERO_MISSION.data.layout.preset_describer.format_params(preset.configuration)

    # Assert
    assert dict(result) == {
        "Gameplay": ["Starts at Brinstar - Starting Room"],
        "Pickup Pool": ["Size: 102 of 102", "Unmodified starting pickup"],
        "Logic Settings": ["All tricks disabled"],
    }
