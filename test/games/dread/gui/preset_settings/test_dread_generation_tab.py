import dataclasses
import uuid
from unittest.mock import MagicMock

from PySide6 import QtCore

from randovania.game_description import default_database
from randovania.games.dread.gui.preset_settings.dread_generation_tab import PresetDreadGeneration
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.games.game import RandovaniaGame
from randovania.interface_common.preset_editor import PresetEditor


def test_on_preset_changed(skip_qtbot, preset_manager):
    # Setup
    game = RandovaniaGame.METROID_DREAD

    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    editor = PresetEditor(preset)
    window = PresetDreadGeneration(editor, default_database.game_description_for(game), MagicMock())
    skip_qtbot.addWidget(window)

    # Run
    window.on_preset_changed(editor.create_custom_preset_with())
    skip_qtbot.mouseClick(window.highdanger_logic_check, QtCore.Qt.LeftButton)

    # Assert
    final_preset = editor.create_custom_preset_with()
    assert isinstance(final_preset.configuration, DreadConfiguration)
    assert final_preset.configuration.allow_highly_dangerous_logic
