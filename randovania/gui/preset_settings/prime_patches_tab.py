from PySide2 import QtWidgets

from randovania.gui.generated.preset_prime_patches_ui import Ui_PresetPrimePatches
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class PresetPrimePatches(PresetTab, Ui_PresetPrimePatches):
    _editor: PresetEditor

    def __init__(self, editor: PresetEditor):
        super().__init__()
        self.setupUi(self)
        self._editor = editor

        self.description_label.setText(self.description_label.text().replace("color:#0000ff;", ""))

        # Signals
        self._add_persist_option(self.qol_game_breaking_check, "qol_game_breaking")
        self._add_persist_option(self.qol_logical_check, "qol_logical")
        self._add_persist_option(self.qol_major_cutscenes_check, "qol_major_cutscenes")
        self._add_persist_option(self.qol_minor_cutscenes_check, "qol_minor_cutscenes")

    @property
    def uses_patches_tab(self) -> bool:
        return True

    def _add_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str):
        def persist(value: bool):
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        self.qol_game_breaking_check.setChecked(config.qol_game_breaking)
        self.qol_logical_check.setChecked(config.qol_logical)
        self.qol_major_cutscenes_check.setChecked(config.qol_major_cutscenes)
        self.qol_minor_cutscenes_check.setChecked(config.qol_minor_cutscenes)
