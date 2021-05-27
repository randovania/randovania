from PySide2 import QtCore

from randovania.gui.generated.preset_prime_goal_ui import Ui_PresetPrimeGoal
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset
from randovania.layout.prime1.artifact_mode import LayoutArtifactMode


class PresetPrimeGoal(PresetTab, Ui_PresetPrimeGoal):
    _editor: PresetEditor

    def __init__(self, editor: PresetEditor):
        super().__init__()
        self.setupUi(self)
        self._editor = editor

        self.goal_layout.setAlignment(QtCore.Qt.AlignTop)
        self.slider.valueChanged.connect(self._on_slider_changed)

    @property
    def uses_patches_tab(self) -> bool:
        return False

    def _update_editor(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "artifacts",
                LayoutArtifactMode(self.slider.value())
            )

    def _on_slider_changed(self):
        self.slider_label.setText(str(self.slider.value()))
        self._update_editor()

    def on_preset_changed(self, preset: Preset):
        artifacts = preset.configuration.artifacts
        self.slider.setValue(artifacts.num_artifacts)
