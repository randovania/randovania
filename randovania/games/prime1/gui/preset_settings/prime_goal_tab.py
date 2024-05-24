from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.prime1.gui.generated.preset_prime_goal_ui import Ui_PresetPrimeGoal
from randovania.games.prime1.layout.artifact_mode import LayoutArtifactMode
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetPrimeGoal(PresetTab, Ui_PresetPrimeGoal):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.placed_slider.valueChanged.connect(self._on_placed_slider_changed)
        self.required_slider.valueChanged.connect(self._on_required_slider_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    def _update_editor(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("artifact_target", LayoutArtifactMode(self.placed_slider.value()))
            editor.set_configuration_field("artifact_required", LayoutArtifactMode(self.required_slider.value()))

    def _on_placed_slider_changed(self) -> None:
        self.placed_slider_label.setText(str(self.placed_slider.value()))
        self._update_editor()

    def _on_required_slider_changed(self) -> None:
        self.required_slider_label.setText(str(self.required_slider.value()))
        self._update_editor()

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, PrimeConfiguration)
        placed = config.artifact_target
        required = config.artifact_required
        self.placed_slider.setValue(placed.num_artifacts)
        self.required_slider.setValue(required.num_artifacts)
