import dataclasses
from typing import Callable

from PySide6 import QtCore

from randovania.game_description.game_description import GameDescription
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration, AM2RArtifactConfig
from randovania.gui.generated.preset_am2r_goal_ui import Ui_PresetAM2RGoal
from randovania.gui.lib import signal_handling
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class PresetAM2RGoal(PresetTab, Ui_PresetAM2RGoal):

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignTop)
        signal_handling.on_checked(self.prefer_metroids_check, self._on_prefer_metroids)
        signal_handling.on_checked(self.prefer_bosses_check, self._on_prefer_bosses)
        self.dna_slider.valueChanged.connect(self._on_dna_slider_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    def _update_slider_max(self):
        self.dna_slider.setMaximum(self.num_preferred_locations)
        self.dna_slider.setEnabled(self.num_preferred_locations > 0)

    def _edit_config(self, call: Callable[[AM2RArtifactConfig], AM2RArtifactConfig]):
        config = self._editor.configuration
        assert isinstance(config, AM2RConfiguration)

        with self._editor as editor:
            editor.set_configuration_field(
                "artifacts",
                call(config.artifacts)
            )

    @property
    def num_preferred_locations(self) -> int:
        if self.prefer_metroids_check.isChecked():
           return 46
        if self.prefer_bosses_check.isChecked():
            return 6
        return 0


    def _on_prefer_metroids(self, value: bool):
        def edit(config: AM2RArtifactConfig):
            return dataclasses.replace(config, prefer_metroids=value)

        self._edit_config(edit)
        self._update_slider_max()

    def _on_prefer_bosses(self, value: bool):
        def edit(config: AM2RArtifactConfig):
            return dataclasses.replace(config, prefer_bosses=value)

        self._edit_config(edit)
        self._update_slider_max()

    def _on_dna_slider_changed(self):
        self.dna_slider_label.setText(f"{self.dna_slider.value()} DNA")

        def edit(config: AM2RArtifactConfig):
            return dataclasses.replace(config,
                                       required_artifacts=self.dna_slider.value())

        self._edit_config(edit)

    def on_preset_changed(self, preset: Preset):
        assert isinstance(preset.configuration, AM2RConfiguration)
        artifacts = preset.configuration.artifacts
        self.prefer_metroids_check.setChecked(artifacts.prefer_metroids)
        self.prefer_bosses_check.setChecked(artifacts.prefer_bosses)
        self.dna_slider.setValue(artifacts.required_artifacts)

