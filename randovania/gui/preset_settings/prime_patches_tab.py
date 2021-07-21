import typing

from PySide2 import QtWidgets

from randovania.gui.generated.preset_prime_patches_ui import Ui_PresetPrimePatches
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset
from randovania.layout.prime1.prime_configuration import LayoutCutsceneMode

_FIELDS = [
    "warp_to_start",
    "main_plaza_door",
    "backwards_frigate",
    "backwards_labs",
    "backwards_upper_mines",
    "backwards_lower_mines",
    "phazon_elite_without_dynamo",
    "qol_game_breaking",
    "small_samus",
]


class PresetPrimePatches(PresetTab, Ui_PresetPrimePatches):
    _editor: PresetEditor

    def __init__(self, editor: PresetEditor):
        super().__init__()
        self.setupUi(self)
        self._editor = editor

        self.description_label.setText(self.description_label.text().replace("color:#0000ff;", ""))

        # Signals
        self.cutscene_combo.setItemData(0, LayoutCutsceneMode.ORIGINAL)
        self.cutscene_combo.setItemData(1, LayoutCutsceneMode.MINOR)
        self.cutscene_combo.setItemData(2, LayoutCutsceneMode.MAJOR)
        signal_handling.on_combo(self.cutscene_combo, self._on_cutscene_changed)
        for f in _FIELDS:
            self._add_persist_option(getattr(self, f"{f}_check"), f)

    @property
    def uses_patches_tab(self) -> bool:
        return True

    def _add_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str):
        def persist(value: bool):
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def _on_cutscene_changed(self, value: LayoutCutsceneMode):
        with self._editor as editor:
            editor.set_configuration_field("qol_cutscenes", value)

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        for f in _FIELDS:
            typing.cast(QtWidgets.QCheckBox, getattr(self, f"{f}_check")).setChecked(getattr(config, f))
        signal_handling.combo_set_to_value(self.cutscene_combo, config.qol_cutscenes)
