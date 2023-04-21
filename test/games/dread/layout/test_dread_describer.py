import dataclasses

import pytest

from randovania.games.dread.layout.dread_configuration import DreadConfiguration, DreadArtifactConfig
from randovania.games.game import RandovaniaGame
from randovania.interface_common.preset_manager import PresetManager


@pytest.mark.parametrize("has_artifacts", [False, True])
def test_dread_format_params(has_artifacts):
    # Setup
    preset = PresetManager(None).default_preset_for_game(RandovaniaGame.METROID_DREAD).get_preset()
    assert isinstance(preset.configuration, DreadConfiguration)
    configuration = dataclasses.replace(
        preset.configuration,
        artifacts=DreadArtifactConfig(
            prefer_emmi=True,
            prefer_major_bosses=False,
            required_artifacts=3 if has_artifacts else 0,
        )
    )

    # Run
    result = RandovaniaGame.METROID_DREAD.data.layout.preset_describer.format_params(configuration)

    # Assert
    assert dict(result) == {
        "Difficulty": [
            "Damage Strictness: Medium",
            "Immediate Energy Part"
        ],
        "Game Changes": [
            "Open Hanubia Shortcut, Easier Path to Itorash in Hanubia",
        ],
        "Environmental Damage": [
            "Heat: Constant 20 dmg/s",
            "Cold: Constant 20 dmg/s",
            "Lava: Constant 20 dmg/s",
        ],
        "Gameplay": [
            "Starting Location: Artaria - Intro Room"
        ],
        "Goal": ["3 Metroid DNA", "Prefers E.M.M.I."] if has_artifacts else ["Reach Itorash"],
        "Item Pool": [
            "Size: 148 of 149" if has_artifacts else "Size: 145 of 149",
            "No Pulse Radar",
            "Progressive Beam, Progressive Charge Beam, Progressive Missile, "
            "Progressive Bomb, Progressive Suit, Progressive Spin"
        ],
        "Logic Settings": [
            "All tricks disabled",
            "Dangerous Actions: Randomly"
        ],
        "Starting Items": [
            "Pulse Radar"
        ]
    }
