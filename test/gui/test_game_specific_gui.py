from unittest.mock import MagicMock

from randovania.games.game import RandovaniaGame
from randovania.gui import game_specific_gui
from randovania.interface_common.preset_editor import PresetEditor


def test_preset_editor_tabs_for(skip_qtbot, game_enum: RandovaniaGame, preset_manager):
    preset = preset_manager.default_preset_for_game(game_enum)
    editor = PresetEditor(preset.get_preset().fork())
    window_manager = MagicMock()

    # Run
    result = game_specific_gui.preset_editor_tabs_for(editor, window_manager)

    # Assert
    assert len(result) > 4
