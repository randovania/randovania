from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.games.blank.layout import BlankConfiguration
from randovania.games.game import RandovaniaGame

if TYPE_CHECKING:
    from randovania.interface_common.preset_manager import PresetManager


def test_dangerous_settings(preset_manager):
    configuration = preset_manager.default_preset_for_game(RandovaniaGame.BLANK).get_preset().configuration
    dangerous_config = dataclasses.replace(configuration, first_progression_must_be_local=True)

    # Run
    no_dangerous = configuration.dangerous_settings()
    has_dangerous = dangerous_config.dangerous_settings()

    # Assert
    assert no_dangerous == []
    assert has_dangerous == ["Requiring first progression to be local causes increased generation failure."]


def test_without_broken_settings_no_change(preset_manager: PresetManager) -> None:
    preset = preset_manager.default_preset_for_game(RandovaniaGame.BLANK).get_preset()
    assert preset.without_broken_settings() is preset


def test_without_broken_settings_remove(preset_manager: PresetManager) -> None:
    base_preset = preset_manager.default_preset_for_game(RandovaniaGame.BLANK).get_preset()
    configuration = base_preset.configuration
    assert isinstance(configuration, BlankConfiguration)

    bad_preset = dataclasses.replace(
        base_preset,
        configuration=dataclasses.replace(
            configuration,
            include_extra_pickups=True,
            break_extra_pickups=True,
        ),
    )
    fixed_preset = bad_preset.without_broken_settings()

    assert bad_preset is not fixed_preset
    assert bad_preset.configuration != fixed_preset.configuration
    assert fixed_preset.configuration == dataclasses.replace(
        configuration,
        break_extra_pickups=True,
    )
