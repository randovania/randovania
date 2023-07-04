import logging

from PySide6 import QtWidgets

from randovania.games.game import RandovaniaGame
from randovania.gui.generated.select_preset_dialog_ui import Ui_SelectPresetDialog
from randovania.gui.lib import common_qt_lib, signal_handling
from randovania.interface_common.options import Options
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout import preset_describer
from randovania.layout.versioned_preset import VersionedPreset, InvalidPreset
from randovania.lib.migration_lib import UnsupportedVersion
from randovania.network_common.multiplayer_session import MAX_WORLD_NAME_LENGTH, WORLD_NAME_RE


class SelectPresetDialog(QtWidgets.QDialog, Ui_SelectPresetDialog):
    valid_preset: bool

    def __init__(self, preset_manager: PresetManager, options: Options, *,
                 allowed_games: list[RandovaniaGame] | None = None,
                 include_world_name_prompt: bool = False):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.include_world_name_prompt = include_world_name_prompt
        self.world_name_edit.setVisible(include_world_name_prompt)
        self.world_name_label.setVisible(include_world_name_prompt)

        self.allowed_games = allowed_games or list(RandovaniaGame.all_games())
        for game in self.allowed_games:
            self.game_selection_combo.addItem(game.long_name, game)

        self.create_preset_tree.game = self.allowed_games[0]
        self.create_preset_tree.preset_manager = preset_manager
        self.create_preset_tree.options = options

        signal_handling.on_combo(self.game_selection_combo, self._on_select_game)
        self.create_preset_tree.itemSelectionChanged.connect(self._on_select_preset)
        # self.create_preset_tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.world_name_edit.textEdited.connect(self.update_accept_button)
        self.world_name_edit.setMaxLength(MAX_WORLD_NAME_LENGTH)

        self.create_preset_tree.update_items()
        self.valid_preset = False
        self.on_preset_changed(None)

    @property
    def selected_preset(self) -> VersionedPreset | None:
        return self.create_preset_tree.current_preset_data

    def _on_select_game(self, _):
        game: RandovaniaGame = self.game_selection_combo.currentData()
        self.create_preset_tree.game = game
        self.create_preset_tree.update_items()
        self.on_preset_changed(None)

    def _on_select_preset(self):
        self.on_preset_changed(self.selected_preset)

    def on_preset_changed(self, preset: VersionedPreset | None):
        can_generate = False
        if preset is None:
            description = "Please select a preset from the list."

        else:
            try:
                raw_preset = preset.get_preset()
                can_generate = True
                description = f"<p style='font-weight:600;'>{raw_preset.name}</p><p>{raw_preset.description}</p>"
                description += preset_describer.merge_categories(preset_describer.describe(raw_preset))

            except InvalidPreset as e:
                if not isinstance(e.original_exception, UnsupportedVersion):
                    logging.exception(f"Invalid preset for {preset.name}")
                description = (
                    f"Preset {preset.name} can't be used as it contains the following error:"
                    f"\n{e.original_exception}\n"
                    f"\nPlease open edit the preset file with id {preset.uuid} manually or delete this preset."
                )

        self.create_preset_description.setText(description)
        self.valid_preset = can_generate
        self.update_accept_button()

    def update_accept_button(self):
        can_accept = self.valid_preset

        if self.include_world_name_prompt:
            valid_name = WORLD_NAME_RE.match(self.world_name_edit.text()) is not None
            common_qt_lib.set_error_border_stylesheet(self.world_name_edit, not valid_name)
            can_accept = can_accept and valid_name

        self.accept_button.setEnabled(can_accept)
