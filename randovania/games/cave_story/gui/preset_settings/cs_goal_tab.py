from PySide2 import QtCore

from randovania.games.cave_story.layout.cs_configuration import CSObjective
from randovania.gui.generated.preset_cs_objective_ui import Ui_PresetCSObjective
from randovania.gui.lib.common_qt_lib import set_combo_with_value
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class PresetCSObjective(PresetTab, Ui_PresetCSObjective):
    def __init__(self, editor: PresetEditor) -> None:
        super().__init__(editor)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignTop)
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
    def uses_patches_tab(cls) -> bool:
        return False

    def _on_objective_changed(self):
        combo_enum = self.goal_combo.currentData()
        with self._editor as editor:
            editor.set_configuration_field("objective", combo_enum)
            self.b2_check.setVisible(combo_enum.enters_hell)

    def _on_blocks_changed(self):
        disabled = self.b2_check.isChecked()
        with self._editor as editor:
            editor.set_configuration_field("no_blocks", disabled)

    def on_preset_changed(self, preset: Preset):
        set_combo_with_value(self.goal_combo, preset.configuration.objective)
        self.b2_check.setChecked(preset.configuration.no_blocks)
