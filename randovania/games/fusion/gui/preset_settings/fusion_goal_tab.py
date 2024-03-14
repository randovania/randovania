from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.fusion.layout.fusion_configuration import FusionArtifactConfig, FusionConfiguration
from randovania.gui.generated.preset_fusion_goal_ui import Ui_PresetFusionGoal
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetFusionGoal(PresetTab, Ui_PresetFusionGoal):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.restrict_placement_radiobutton.toggled.connect(self._on_restrict_placement)
        self.free_placement_radiobutton.toggled.connect(self._on_free_placement)
        signal_handling.on_checked(self.prefer_bosses_check, self._on_prefer_bosses)
        self.required_slider.valueChanged.connect(self._on_required_slider_changed)
        self.placed_slider.valueChanged.connect(self._on_placed_slider_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    def _update_slider_max(self) -> None:
        self.placed_slider.setMaximum(self.num_preferred_locations)
        self.placed_slider.setEnabled(self.num_preferred_locations > 0)

    def _edit_config(self, call: Callable[[FusionArtifactConfig], FusionArtifactConfig]) -> None:
        config = self._editor.configuration
        assert isinstance(config, FusionConfiguration)

        with self._editor as editor:
            editor.set_configuration_field("artifacts", call(config.artifacts))

    @property
    def num_preferred_locations(self) -> int:
        if self.free_placement_radiobutton.isChecked():
            return 20
        if self.prefer_bosses_check.isChecked():
            return 11
        return 0

    def _on_restrict_placement(self, value: bool) -> None:
        if not value:
            return
        self.prefer_bosses_check.setEnabled(True)

        def edit(config: FusionArtifactConfig) -> FusionArtifactConfig:
            return dataclasses.replace(config, prefer_anywhere=False)

        self._edit_config(edit)
        self._update_slider_max()

    def _on_free_placement(self, value: bool) -> None:
        if not value:
            return
        self.prefer_bosses_check.setEnabled(False)

        def edit(config: FusionArtifactConfig) -> FusionArtifactConfig:
            return dataclasses.replace(config, prefer_anywhere=True)

        self._edit_config(edit)
        self._update_slider_max()

    def _on_prefer_bosses(self, value: bool) -> None:
        def edit(config: FusionArtifactConfig) -> FusionArtifactConfig:
            return dataclasses.replace(config, prefer_bosses=value)

        self._edit_config(edit)
        self._update_slider_max()

    def _on_required_slider_changed(self) -> None:
        self.required_slider_label.setText(f"{self.required_slider.value()} Metroids Required")

        def edit(config: FusionArtifactConfig) -> FusionArtifactConfig:
            return dataclasses.replace(config, required_artifacts=self.required_slider.value())

        self._edit_config(edit)

    def _on_placed_slider_changed(self) -> None:
        self.placed_slider_label.setText(f"{self.placed_slider.value()} Metroids in Pool")
        self.required_slider.setMaximum(self.placed_slider.value())
        self.required_slider.setEnabled(self.placed_slider.value() > 0)

        def edit(config: FusionArtifactConfig) -> FusionArtifactConfig:
            return dataclasses.replace(config, placed_artifacts=self.placed_slider.value())

        self._edit_config(edit)

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, FusionConfiguration)
        artifacts = preset.configuration.artifacts
        self.free_placement_radiobutton.setChecked(artifacts.prefer_anywhere)
        self.restrict_placement_radiobutton.setChecked(not artifacts.prefer_anywhere)
        self.prefer_bosses_check.setChecked(artifacts.prefer_bosses)
        self.required_slider.setValue(artifacts.required_artifacts)
        self.placed_slider.setValue(artifacts.placed_artifacts)
