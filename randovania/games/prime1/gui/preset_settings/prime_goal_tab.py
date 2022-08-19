from PySide6 import QtCore

from randovania.game_description.game_description import GameDescription
from randovania.games.prime1.layout.artifact_mode import LayoutArtifactMode
from randovania.gui.generated.preset_prime_goal_ui import Ui_PresetPrimeGoal
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class PresetPrimeGoal(PresetTab, Ui_PresetPrimeGoal):

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignTop)
        self.slider.valueChanged.connect(self._on_slider_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    def _update_editor(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "artifact_target",
                LayoutArtifactMode(self.slider.value())
            )

    def _on_slider_changed(self):
        self.slider_label.setText(str(self.slider.value()))
        self._update_editor()

    def on_preset_changed(self, preset: Preset):
        artifacts = preset.configuration.artifact_target
        self.slider.setValue(artifacts.num_artifacts)
