from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.games.prime1.gui.preset_settings.prime_generation_tab import _CHECKBOX_FIELDS, PresetPrimeGeneration
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.interface_common.preset_editor import PresetEditor


def test_on_preset_changed(skip_qtbot, preset_manager):
    # Setup
    game = RandovaniaGame.METROID_PRIME
    options = MagicMock()

    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    editor = PresetEditor(preset, options)
    window = PresetPrimeGeneration(editor, default_database.game_description_for(game), MagicMock())
    skip_qtbot.addWidget(window)

    # Run enabling all Prime checkboxes
    window.on_preset_changed(editor.create_custom_preset_with())
    for f in _CHECKBOX_FIELDS:
        getattr(window, f + "_check").setChecked(True)

    # Assert
    all_enabled_preset = editor.create_custom_preset_with()
    assert isinstance(all_enabled_preset.configuration, PrimeConfiguration)
    for f in _CHECKBOX_FIELDS:
        assert getattr(all_enabled_preset.configuration, f) is True

    # Run disabling all Prime checkboxes
    for f in _CHECKBOX_FIELDS:
        getattr(window, f + "_check").setChecked(False)

    # Assert
    all_disabled_preset = editor.create_custom_preset_with()
    assert isinstance(all_disabled_preset.configuration, PrimeConfiguration)
    for f in _CHECKBOX_FIELDS:
        assert getattr(all_disabled_preset.configuration, f) is False
