from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from randovania.gui import game_specific_gui
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout import filtered_database

if TYPE_CHECKING:
    from randovania.games.game import RandovaniaGame


def test_preset_editor_tabs_for(skip_qtbot, game_enum: RandovaniaGame, preset_manager):
    preset = preset_manager.default_preset_for_game(game_enum)
    options = MagicMock()
    editor = PresetEditor(preset.get_preset().fork(), options)
    window_manager = MagicMock()
    game = filtered_database.game_description_for_layout(preset.get_preset().configuration)

    # Run
    tabs = list(game_specific_gui.preset_editor_tabs_for(editor, window_manager))

    for it in tabs:
        assert issubclass(it, PresetTab)
        tab = it(editor, game, window_manager)
        tab.on_preset_changed(preset.get_preset())
        skip_qtbot.addWidget(tab)

    # Assert
    assert len(tabs) >= 2
