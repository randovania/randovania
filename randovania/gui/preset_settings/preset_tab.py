import dataclasses
from randovania.interface_common.preset_editor import PresetEditor
from PySide2 import QtWidgets

from randovania.layout.preset import Preset


class PresetTab(QtWidgets.QMainWindow):
    def __init__(self, editor: PresetEditor) -> None:
        super().__init__()
        self._editor = editor

    @property
    def tab_title(self):
        return self.windowTitle()

    @property
    def uses_patches_tab(self) -> bool:
        raise NotImplementedError()

    def on_preset_changed(self, preset: Preset):
        raise NotImplementedError()

    # Persistence helpers
    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            with self._editor as options:
                setattr(options, attribute_name, bool(value))

        return persist

    def _persist_float(self, attribute_name: str):
        def persist(value: float):
            with self._editor as options:
                options.set_configuration_field(attribute_name, value)

        return persist
