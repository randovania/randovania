from unittest.mock import MagicMock

from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.select_preset_dialog import SelectPresetDialog


def test_select_preset_single_game(skip_qtbot, preset_manager):
    game = RandovaniaGame.METROID_PRIME_ECHOES

    options = MagicMock()
    dialog = SelectPresetDialog(preset_manager, options, allowed_games=[game])
    skip_qtbot.add_widget(dialog)

    assert not dialog.accept_button.isEnabled()

    dialog.create_preset_tree.select_preset(
        preset_manager.default_preset_for_game(game)
    )

    assert dialog.accept_button.isEnabled()
    assert dialog.selected_preset == preset_manager.default_preset_for_game(game)


def test_select_preset_two_games_with_name(skip_qtbot, preset_manager):
    game = RandovaniaGame.METROID_PRIME_ECHOES

    options = MagicMock()
    dialog = SelectPresetDialog(preset_manager, options, allowed_games=[RandovaniaGame.BLANK, game],
                                include_world_name_prompt=True)
    skip_qtbot.add_widget(dialog)

    assert not dialog.accept_button.isEnabled()
    dialog.game_selection_combo.setCurrentIndex(1)

    dialog.create_preset_tree.select_preset(
        preset_manager.default_preset_for_game(game)
    )

    assert not dialog.accept_button.isEnabled()
    assert dialog.selected_preset == preset_manager.default_preset_for_game(game)

    dialog.world_name_edit.setText("The Name")
    dialog.update_accept_button()
    assert dialog.accept_button.isEnabled()
