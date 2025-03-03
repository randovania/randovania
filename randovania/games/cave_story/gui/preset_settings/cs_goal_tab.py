from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.cave_story.gui.generated.preset_cs_objective_ui import Ui_PresetCSObjective
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration, CSObjective
from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetCSObjective(PresetTab, Ui_PresetCSObjective):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        for obj in CSObjective:
            if obj == CSObjective.HUNDRED_PERCENT:
                continue  # disabled for now
            self.goal_combo.setItemData(obj.value, obj)

        self.goal_combo.currentIndexChanged.connect(self._on_objective_changed)
        self.b2_check.stateChanged.connect(self._on_blocks_changed)

        # Default to False, since the default objective is Normal Ending
        self.b2_check.setVisible(False)

    @classmethod
    def tab_title(cls) -> str:
        return "Objective"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _on_objective_changed(self) -> None:
        combo_enum = self.goal_combo.currentData()
        with self._editor as editor:
            editor.set_configuration_field("objective", combo_enum)
            self.b2_check.setVisible(combo_enum.enters_hell)

    def _on_blocks_changed(self) -> None:
        disabled = self.b2_check.isChecked()
        with self._editor as editor:
            editor.set_configuration_field("no_blocks", disabled)

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, CSConfiguration)

        set_combo_with_value(self.goal_combo, preset.configuration.objective)
        self.b2_check.setChecked(preset.configuration.no_blocks)
