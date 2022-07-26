import typing

from PySide6 import QtWidgets

from randovania.gui.generated.preset_dread_patches_ui import Ui_PresetDreadPatches
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset

_FIELDS = [
    "hanubia_shortcut_no_grapple",
    "hanubia_easier_path_to_itorash",
    "x_starts_released",
]


class PresetDreadPatches(PresetTab, Ui_PresetDreadPatches):
    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        self.setupUi(self)

        # Signals
        for f in _FIELDS:
            self._add_persist_option(getattr(self, f"{f}_check"), f)

    @classmethod
    def tab_title(cls) -> str:
        return "Other"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def _add_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str):
        def persist(value: bool):
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        for f in _FIELDS:
            typing.cast(QtWidgets.QCheckBox, getattr(self, f"{f}_check")).setChecked(getattr(config, f))
