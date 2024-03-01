from __future__ import annotations

import dataclasses

import pytest

from randovania.games.dread.layout.dread_configuration import (
    DreadArtifactConfig,
    DreadConfiguration,
    DreadRavenBeakDamageMode,
)
from randovania.games.game import RandovaniaGame
from randovania.interface_common.preset_manager import PresetManager


@pytest.mark.parametrize(
    ("has_artifacts", "rb_damage_mode"),
    [
        (False, DreadRavenBeakDamageMode.CONSISTENT_LOW),
        (True, DreadRavenBeakDamageMode.CONSISTENT_LOW),
        (False, DreadRavenBeakDamageMode.CONSISTENT_HIGH),
        (False, DreadRavenBeakDamageMode.UNMODIFIED),
    ],
)
def test_dread_format_params(has_artifacts: bool, rb_damage_mode: DreadRavenBeakDamageMode):
    # Setup
    preset = PresetManager(None).default_preset_for_game(RandovaniaGame.METROID_DREAD).get_preset()
    assert isinstance(preset.configuration, DreadConfiguration)
    configuration = dataclasses.replace(
        preset.configuration,
        artifacts=DreadArtifactConfig(
            prefer_emmi=True,
            prefer_major_bosses=False,
            required_artifacts=3 if has_artifacts else 0,
        ),
        raven_beak_damage_table_handling=rb_damage_mode,
    )

    # Run
    result = RandovaniaGame.METROID_DREAD.data.layout.preset_describer.format_params(configuration)

    # Assert
    assert dict(result) == {
        "Difficulty": ["Immediate Energy Part"],
        "Game Changes": _get_expected_game_changes_text(rb_damage_mode),
        "Environmental Damage": [
            "Heat: Constant 20 dmg/s",
            "Cold: Constant 20 dmg/s",
            "Lava: Constant 20 dmg/s",
        ],
        "Gameplay": ["Starts at Artaria - Intro Room"],
        "Goal": ["3 Metroid DNA", "Prefers E.M.M.I."] if has_artifacts else ["Reach Itorash"],
        "Item Pool": [
            "Size: 148 of 149" if has_artifacts else "Size: 145 of 149",
            "Starts with Pulse Radar",
            "Progressive Charge Beam, Progressive Suit, Progressive Bomb, Progressive Spin",
        ],
        "Logic Settings": ["All tricks disabled"],
    }


def _get_expected_game_changes_text(rb_damage_mode: DreadRavenBeakDamageMode):
    if rb_damage_mode == DreadRavenBeakDamageMode.UNMODIFIED:
        return [
            "Open Hanubia Shortcut, Easier Path to Itorash in Hanubia",
            "Raven Beak Damage: Unmodified",
            "Power Bomb Limitations",
        ]
    elif rb_damage_mode == DreadRavenBeakDamageMode.CONSISTENT_HIGH:
        return [
            "Open Hanubia Shortcut, Easier Path to Itorash in Hanubia",
            "Raven Beak Damage: Consistent, without damage reduction",
            "Power Bomb Limitations",
        ]
    else:
        return [
            "Open Hanubia Shortcut, Easier Path to Itorash in Hanubia",
            "Power Bomb Limitations",
        ]
