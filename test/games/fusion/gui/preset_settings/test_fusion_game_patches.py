from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

from PySide6 import QtWidgets

from randovania.game_description import default_database
from randovania.games.fusion.gui.preset_settings.fusion_patches_tab import _FIELDS, PresetFusionPatches
from randovania.games.fusion.layout.fusion_configuration import FusionConfiguration
from randovania.games.game import RandovaniaGame
from randovania.interface_common.preset_editor import PresetEditor


def test_on_preset_changed(skip_qtbot, preset_manager):
    # Setup
    game = RandovaniaGame.FUSION
    options = MagicMock()

    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("bb84005f-b0f1-4e7e-8057-f4275ff4b2a3"))
    editor = PresetEditor(preset, options)
    window = PresetFusionPatches(editor, default_database.game_description_for(game), MagicMock())
    skip_qtbot.addWidget(window)

    checkboxes = window.findChildren(QtWidgets.QCheckBox)
    assert len(checkboxes) == len(_FIELDS)

    # Run enabling all checkboxes
    window.on_preset_changed(editor.create_custom_preset_with())
    for f in _FIELDS:
        getattr(window, f + "_check").setChecked(True)

    # Assert
    all_enabled_preset = editor.create_custom_preset_with()
    assert isinstance(all_enabled_preset.configuration, FusionConfiguration)
    for f in _FIELDS:
        assert getattr(all_enabled_preset.configuration, f) is True

    # Run disabling all checkboxes
    for f in _FIELDS:
        getattr(window, f + "_check").setChecked(False)

    # Assert
    all_disabled_preset = editor.create_custom_preset_with()
    assert isinstance(all_disabled_preset.configuration, FusionConfiguration)
    for f in _FIELDS:
        assert getattr(all_disabled_preset.configuration, f) is False
