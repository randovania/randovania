from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.am2r.gui.generated.preset_am2r_chaos_ui import Ui_PresetAM2RChaos
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetAM2RChaos(PresetTab, Ui_PresetAM2RChaos):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager) -> None:
        super().__init__(editor, game_description, window_manager)

        self.setupUi(self)
        self.darkness_slider.valueChanged.connect(self._on_slider_changed)
        self.darkness_min_spin.valueChanged.connect(self._on_darkness_spin_changed)
        self.darkness_max_spin.valueChanged.connect(self._on_darkness_spin_changed)
        self.submerged_water_slider.valueChanged.connect(self._on_slider_changed)
        self.submerged_lava_slider.valueChanged.connect(self._on_slider_changed)

        self._change_sliders()

    def _on_darkness_spin_changed(self) -> None:
        self.darkness_min_spin.setMaximum(self.darkness_max_spin.value())
        self.darkness_max_spin.setMinimum(self.darkness_min_spin.value())
        with self._editor as editor:
            editor.set_configuration_field("darkness_min", self.darkness_min_spin.value())
            editor.set_configuration_field("darkness_max", self.darkness_max_spin.value())

    def _on_slider_changed(self):
        self._change_sliders()
        self._update_editor()

    def _change_sliders(self) -> None:
        self.submerged_water_slider.setMaximum(1000 - (self.submerged_lava_slider.value()))
        self.submerged_water_slider.setEnabled(self.submerged_water_slider.maximum() > 0)
        self.submerged_lava_slider.setMaximum(1000 - (self.submerged_water_slider.value()))
        self.submerged_lava_slider.setEnabled(self.submerged_lava_slider.maximum() > 0)

        self.darkness_slider_label.setText(f"{self.darkness_slider.value() / 10.0:.1f}%")
        self.submerged_water_slider_label.setText(f"{self.submerged_water_slider.value() / 10.0:.1f}%")
        self.submerged_lava_slider_label.setText(f"{self.submerged_lava_slider.value() / 10.0:.1f}%")

    @classmethod
    def tab_title(cls) -> str:
        return "Chaos Settings"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, AM2RConfiguration)
        self.darkness_min_spin.setValue(preset.configuration.darkness_min)
        self.darkness_max_spin.setValue(preset.configuration.darkness_max)

        self.darkness_slider.setValue(preset.configuration.darkness_chance)
        self.submerged_water_slider.setValue(preset.configuration.submerged_water_chance)
        self.submerged_lava_slider.setValue(preset.configuration.submerged_lava_chance)

    def _update_editor(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("darkness_chance", self.darkness_slider.value())
            editor.set_configuration_field("submerged_water_chance", self.submerged_water_slider.value())
            editor.set_configuration_field("submerged_lava_chance", self.submerged_lava_slider.value())
