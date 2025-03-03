from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.dread.gui.generated.preset_dread_goal_ui import Ui_PresetDreadGoal
from randovania.games.dread.layout.dread_configuration import DreadArtifactConfig, DreadConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetDreadGoal(PresetTab, Ui_PresetDreadGoal):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        signal_handling.on_checked(self.prefer_emmi_check, self._on_prefer_emmi)
        signal_handling.on_checked(self.prefer_major_bosses_check, self._on_prefer_major_bosses)
        self.dna_slider.valueChanged.connect(self._on_dna_slider_changed)
        self._update_slider_max()

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _update_slider_max(self) -> None:
        self.dna_slider.setMaximum(self.num_preferred_locations)
        self.dna_slider.setEnabled(self.num_preferred_locations > 0)

    def _edit_config(self, call: Callable[[DreadArtifactConfig], DreadArtifactConfig]) -> None:
        config = self._editor.configuration
        assert isinstance(config, DreadConfiguration)

        with self._editor as editor:
            editor.set_configuration_field("artifacts", call(config.artifacts))

    @property
    def num_preferred_locations(self) -> int:
        preferred = 0
        if self.prefer_emmi_check.isChecked():
            preferred += 6
        if self.prefer_major_bosses_check.isChecked():
            preferred += 6
        return preferred

    def _on_prefer_emmi(self, value: bool) -> None:
        def edit(config: DreadArtifactConfig) -> DreadArtifactConfig:
            return dataclasses.replace(config, prefer_emmi=value)

        self._edit_config(edit)
        self._update_slider_max()

    def _on_prefer_major_bosses(self, value: bool) -> None:
        def edit(config: DreadArtifactConfig) -> DreadArtifactConfig:
            return dataclasses.replace(config, prefer_major_bosses=value)

        self._edit_config(edit)
        self._update_slider_max()

    def _on_dna_slider_changed(self) -> None:
        self.dna_slider_label.setText(f"{self.dna_slider.value()} DNA")

        def edit(config: DreadArtifactConfig) -> DreadArtifactConfig:
            return dataclasses.replace(config, required_artifacts=self.dna_slider.value())

        self._edit_config(edit)

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, DreadConfiguration)
        artifacts = preset.configuration.artifacts
        self.prefer_emmi_check.setChecked(artifacts.prefer_emmi)
        self.prefer_major_bosses_check.setChecked(artifacts.prefer_major_bosses)
        self.dna_slider.setValue(artifacts.required_artifacts)
