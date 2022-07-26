import dataclasses
from typing import Callable

from PySide6 import QtCore

from randovania.games.dread.layout.dread_configuration import DreadConfiguration, DreadArtifactConfig
from randovania.gui.generated.preset_dread_goal_ui import Ui_PresetDreadGoal
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class PresetDreadGoal(PresetTab, Ui_PresetDreadGoal):

    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignTop)
        signal_handling.on_checked(self.prefer_emmi_check, self._on_prefer_emmi)
        signal_handling.on_checked(self.prefer_major_bosses_check, self._on_prefer_major_bosses)
        self.dna_slider.valueChanged.connect(self._on_dna_slider_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    def _edit_config(self, call: Callable[[DreadArtifactConfig], DreadArtifactConfig]):
        config = self._editor.configuration
        assert isinstance(config, DreadConfiguration)

        with self._editor as editor:
            editor.set_configuration_field(
                "artifacts",
                call(config.artifacts)
            )

    def _on_prefer_emmi(self, value: bool):
        def edit(config: DreadArtifactConfig):
            return dataclasses.replace(config, prefer_emmi=value)

        self._edit_config(edit)

    def _on_prefer_major_bosses(self, value: bool):
        def edit(config: DreadArtifactConfig):
            return dataclasses.replace(config, prefer_major_bosses=value)

        self._edit_config(edit)

    def _on_dna_slider_changed(self):
        self.dna_slider_label.setText(f"{self.dna_slider.value()} DNA")

        def edit(config: DreadArtifactConfig):
            return dataclasses.replace(config,
                                       required_artifacts=self.dna_slider.value())

        self._edit_config(edit)

    def on_preset_changed(self, preset: Preset):
        assert isinstance(preset.configuration, DreadConfiguration)
        artifacts = preset.configuration.artifacts
        self.dna_slider.setValue(artifacts.required_artifacts)
        self.prefer_emmi_check.setChecked(artifacts.prefer_emmi)
        self.prefer_major_bosses_check.setChecked(artifacts.prefer_major_bosses)
