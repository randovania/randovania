from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

from PySide6 import QtCore

from randovania.game_description import default_database
from randovania.games.dread.gui.preset_settings.dread_patches_tab import PresetDreadPatches
from randovania.games.dread.layout.dread_configuration import DreadConfiguration, DreadRavenBeakDamageMode
from randovania.games.game import RandovaniaGame
from randovania.interface_common.preset_editor import PresetEditor


def test_on_preset_changed(skip_qtbot, preset_manager):
    # Setup
    game = RandovaniaGame.METROID_DREAD
    options = MagicMock()

    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    editor = PresetEditor(preset, options)
    window = PresetDreadPatches(editor, default_database.game_description_for(game), MagicMock())
    skip_qtbot.addWidget(window)

    # Run
    window.on_preset_changed(editor.create_custom_preset_with())
    skip_qtbot.mouseClick(window.raven_beak_damage_table_handling_check, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    final_preset = editor.create_custom_preset_with()
    assert isinstance(final_preset.configuration, DreadConfiguration)
    assert final_preset.configuration.raven_beak_damage_table_handling == DreadRavenBeakDamageMode.CONSISTENT_HIGH
