from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.samus_returns.layout.msr_configuration import MSRArtifactConfig, MSRConfiguration
from randovania.gui.generated.preset_msr_goal_ui import Ui_PresetMSRGoal
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetMSRGoal(PresetTab, Ui_PresetMSRGoal):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        signal_handling.on_checked(self.prefer_metroids_check, self._on_prefer_metroids)
        self.dna_slider.valueChanged.connect(self._on_dna_slider_changed)
        self.dna_slider.setMaximum(39)

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    def _edit_config(self, call: Callable[[MSRArtifactConfig], MSRArtifactConfig]) -> None:
        config = self._editor.configuration
        assert isinstance(config, MSRConfiguration)

        with self._editor as editor:
            editor.set_configuration_field("artifacts", call(config.artifacts))

    def _on_prefer_metroids(self, value: bool) -> None:
        def edit(config: MSRArtifactConfig) -> MSRArtifactConfig:
            return dataclasses.replace(config, prefer_metroids=value)

        self._edit_config(edit)

    def _on_dna_slider_changed(self) -> None:
        self.dna_slider_label.setText(f"{self.dna_slider.value()} DNA")

        def edit(config: MSRArtifactConfig) -> MSRArtifactConfig:
            return dataclasses.replace(config, required_artifacts=self.dna_slider.value())

        self._edit_config(edit)

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, MSRConfiguration)
        artifacts = preset.configuration.artifacts
        self.prefer_metroids_check.setChecked(artifacts.prefer_metroids)
        self.dna_slider.setValue(artifacts.required_artifacts)
