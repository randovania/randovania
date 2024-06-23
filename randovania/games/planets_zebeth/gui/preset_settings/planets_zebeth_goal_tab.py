from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.planets_zebeth.gui.generated.preset_planets_zebeth_goal_ui import Ui_PresetPlanetsZebethGoal
from randovania.games.planets_zebeth.layout.planets_zebeth_configuration import (
    PlanetsZebethArtifactConfig,
    PlanetsZebethConfiguration,
)
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetPlanetsZebethGoal(PresetTab, Ui_PresetPlanetsZebethGoal):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        signal_handling.on_checked(self.vanilla_tourian_keys_check, self._on_vanilla_tourian_keys)
        self.keys_slider.valueChanged.connect(self._on_keys_slider_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    def _update_slider(self) -> None:
        if self.vanilla_tourian_keys_check.isChecked():
            self.keys_slider.setValue(2)
            self.keys_slider.setEnabled(False)
        else:
            self.keys_slider.setEnabled(True)

    def _edit_config(self, call: Callable[[PlanetsZebethArtifactConfig], PlanetsZebethArtifactConfig]) -> None:
        config = self._editor.configuration
        assert isinstance(config, PlanetsZebethConfiguration)

        with self._editor as editor:
            editor.set_configuration_field("artifacts", call(config.artifacts))

    def _on_vanilla_tourian_keys(self, value: bool) -> None:
        def edit(config: PlanetsZebethArtifactConfig) -> PlanetsZebethArtifactConfig:
            return dataclasses.replace(config, vanilla_tourian_keys=value)

        self._edit_config(edit)
        self._update_slider()

    def _on_keys_slider_changed(self) -> None:
        plural = "s" if self.keys_slider.value() > 1 else ""
        self.keys_slider_label.setText(f"{self.keys_slider.value()} Key{plural}")

        def edit(config: PlanetsZebethArtifactConfig) -> PlanetsZebethArtifactConfig:
            return dataclasses.replace(config, required_artifacts=self.keys_slider.value())

        self._edit_config(edit)

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, PlanetsZebethConfiguration)
        artifacts = preset.configuration.artifacts
        self.vanilla_tourian_keys_check.setChecked(artifacts.vanilla_tourian_keys)
        self.keys_slider.setValue(artifacts.required_artifacts)
        self._update_slider()
