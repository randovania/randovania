import dataclasses
import uuid
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore, QtWidgets

from randovania.game_description import default_database
from randovania.games.cave_story.gui.preset_settings.cs_generation_tab import PresetCSGeneration
from randovania.games.dread.gui.preset_settings.dread_generation_tab import PresetDreadGeneration
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.gui.preset_settings.prime_generation_tab import PresetPrimeGeneration
from randovania.gui.preset_settings.generation_tab import PresetGeneration
from randovania.interface_common.preset_editor import PresetEditor


@pytest.mark.parametrize("game_data", [
    (RandovaniaGame.METROID_DREAD, True, False, PresetDreadGeneration),
    (RandovaniaGame.METROID_PRIME, True, True, PresetPrimeGeneration),
    (RandovaniaGame.METROID_PRIME_ECHOES, False, True, PresetGeneration),
    (RandovaniaGame.CAVE_STORY, True, False, PresetCSGeneration)
])
def test_on_preset_changed(skip_qtbot, preset_manager, game_data):
    # Setup
    game, has_specific_settings, has_min_logic, tab = game_data

    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    editor = PresetEditor(preset)
    window: PresetGeneration = tab(editor, default_database.game_description_for(game), MagicMock())
    parent = QtWidgets.QWidget()
    window.setParent(parent)
    skip_qtbot.addWidget(window)

    # Run
    window.on_preset_changed(editor.create_custom_preset_with())

    # Assert
    assert window.trick_level_minimal_logic_check.isVisibleTo(parent) == has_min_logic
    assert window.game_specific_group.isVisibleTo(parent) == has_specific_settings


def test_persist_local_first_progression(skip_qtbot, preset_manager):
    game = RandovaniaGame.BLANK

    editor = MagicMock()
    window = PresetGeneration(editor, default_database.game_description_for(game), MagicMock())
    skip_qtbot.addWidget(window)

    # Run
    skip_qtbot.mouseClick(window.local_first_progression_check, QtCore.Qt.LeftButton)

    # Assert
    editor.__enter__.return_value.set_configuration_field.assert_called_once_with(
        "first_progression_must_be_local", True)
