from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.game import RandovaniaGame
from randovania.gui.generated.multiplayer_select_preset_dialog_ui import Ui_MultiplayerSelectPresetDialog
from randovania.gui.lib import common_qt_lib, signal_handling
from randovania.network_common.multiplayer_session import MAX_WORLD_NAME_LENGTH, WORLD_NAME_RE

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.options import Options
    from randovania.layout.versioned_preset import VersionedPreset


class MultiplayerSelectPresetDialog(QtWidgets.QDialog, Ui_MultiplayerSelectPresetDialog):
    valid_preset: bool

    def __init__(
        self,
        window_manager: WindowManager,
        options: Options,
        *,
        allowed_games: list[RandovaniaGame] | None = None,
        default_game: RandovaniaGame | None = None,
        include_world_name_prompt: bool = False,
    ):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.include_world_name_prompt = include_world_name_prompt
        self.world_name_edit.setVisible(include_world_name_prompt)
        self.world_name_label.setVisible(include_world_name_prompt)

        self.allowed_games = allowed_games or list(RandovaniaGame.all_games())
        for game in self.allowed_games:
            self.game_selection_combo.addItem(game.long_name, game)
        if default_game is not None:
            signal_handling.set_combo_with_value(self.game_selection_combo, default_game)

        self.select_preset_widget.for_multiworld = True
        self.select_preset_widget.setup_ui(default_game or self.allowed_games[0], window_manager, options)

        signal_handling.on_combo(self.game_selection_combo, self._on_select_game)

        self.select_preset_widget.CanGenerate.connect(self._on_can_generate)
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.world_name_edit.textEdited.connect(self.update_accept_button)
        self.world_name_edit.setMaxLength(MAX_WORLD_NAME_LENGTH)

        self.valid_preset = False
        self.update_accept_button()

    @property
    def selected_preset(self) -> VersionedPreset | None:
        return self.select_preset_widget.preset

    def _on_select_game(self, _):
        game: RandovaniaGame = self.game_selection_combo.currentData()
        self.select_preset_widget.change_game(game)

    def _on_can_generate(self, can_generate: bool):
        self.valid_preset = can_generate
        self.update_accept_button()

    def update_accept_button(self):
        can_accept = self.valid_preset

        if self.include_world_name_prompt:
            valid_name = WORLD_NAME_RE.match(self.world_name_edit.text()) is not None
            common_qt_lib.set_error_border_stylesheet(self.world_name_edit, not valid_name)
            can_accept = can_accept and valid_name

        self.accept_button.setEnabled(can_accept)
