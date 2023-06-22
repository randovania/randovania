from unittest.mock import MagicMock

from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.select_preset_dialog import SelectPresetDialog


def test_select_preset(skip_qtbot, preset_manager):
    game = RandovaniaGame.METROID_PRIME_ECHOES

    options = MagicMock()
    dialog = SelectPresetDialog(game, preset_manager, options)
    skip_qtbot.add_widget(dialog)

    assert not dialog.accept_button.isEnabled()

    dialog.create_preset_tree.select_preset(
        preset_manager.default_preset_for_game(game)
    )

    assert dialog.accept_button.isEnabled()
    assert dialog.selected_preset == preset_manager.default_preset_for_game(game)
