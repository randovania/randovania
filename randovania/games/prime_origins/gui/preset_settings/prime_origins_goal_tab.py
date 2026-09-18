from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.prime_origins.gui.generated.preset_prime_origins_goal_ui import Ui_PresetPrimeOriginsGoal
from randovania.games.prime_origins.layout.prime_origins_configuration import MPOConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetPrimeOriginsGoal(PresetTab, Ui_PresetPrimeOriginsGoal):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.placed_slider.valueChanged.connect(self._on_placed_slider_changed)
        self.required_slider.valueChanged.connect(self._on_required_slider_changed)
        self.main_bosses_checkbox.stateChanged.connect(self._on_checkbox_changed)
        self.mini_bosses_checkbox.stateChanged.connect(self._on_checkbox_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _update_editor(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("artifact_target", self.placed_slider.value())
            editor.set_configuration_field("artifact_required", self.required_slider.value())
            editor.set_configuration_field("main_bosses_required", self.main_bosses_checkbox.isChecked())
            editor.set_configuration_field("mini_bosses_required", self.mini_bosses_checkbox.isChecked())

    def _on_checkbox_changed(self) -> None:
        self._update_editor()

    def _on_placed_slider_changed(self) -> None:
        self.placed_slider_label.setText(str(self.placed_slider.value()))
        self._update_editor()

    def _on_required_slider_changed(self) -> None:
        self.required_slider_label.setText(str(self.required_slider.value()))
        self._update_editor()

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, MPOConfiguration)

        self.placed_slider.setValue(config.artifact_target)
        self.required_slider.setValue(config.artifact_required)
        self.main_bosses_checkbox.setChecked(config.main_bosses_required)
        self.mini_bosses_checkbox.setChecked(config.mini_bosses_required)
