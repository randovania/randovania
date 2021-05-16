from PySide2 import QtWidgets

from randovania.layout.preset import Preset


class PresetTab(QtWidgets.QMainWindow):
    @property
    def tab_title(self):
        return self.windowTitle()

    @property
    def uses_patches_tab(self) -> bool:
        raise NotImplementedError()

    def on_preset_changed(self, preset: Preset):
        raise NotImplementedError()
