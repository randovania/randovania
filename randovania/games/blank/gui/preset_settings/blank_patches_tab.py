from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.blank.layout import BlankConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetBlankPatches(PresetTab[BlankConfiguration]):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)

        self.root_widget = QtWidgets.QWidget(self)
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)

        self.include_extra_pickups_check = QtWidgets.QCheckBox(self.root_widget)
        self.include_extra_pickups_check.setEnabled(True)
        self.include_extra_pickups_check.setText("Include Extra Pickups")
        self.root_layout.addWidget(self.include_extra_pickups_check)

        self.include_extra_pickups_label = QtWidgets.QLabel(self.root_widget)
        self.include_extra_pickups_label.setWordWrap(True)
        self.include_extra_pickups_label.setText("Include some optional pickups.")
        self.root_layout.addWidget(self.include_extra_pickups_label)

        self.setCentralWidget(self.root_widget)

        # Signals
        self.include_extra_pickups_check.stateChanged.connect(self._persist_option_then_notify("include_extra_pickups"))

    @classmethod
    def tab_title(cls) -> str:
        return "Other"

    @classmethod
    def header_name(cls) -> str | None:
        return cls.GAME_MODIFICATIONS_HEADER

    def on_preset_changed(self, preset: Preset[BlankConfiguration]) -> None:
        config = preset.configuration
        self.include_extra_pickups_check.setChecked(config.include_extra_pickups)
