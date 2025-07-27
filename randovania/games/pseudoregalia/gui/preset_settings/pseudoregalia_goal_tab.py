from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.pseudoregalia.gui.generated.preset_pseudoregalia_goal_ui import Ui_PresetPseudoregaliaGoal
from randovania.games.pseudoregalia.layout.pseudoregalia_configuration import PseudoregaliaConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetPseudoregaliaGoal(PresetTab, Ui_PresetPseudoregaliaGoal):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.key_slider.valueChanged.connect(self._on_key_slider_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _on_key_slider_changed(self) -> None:
        count = self.key_slider.value()
        self.key_slider_label.setText(f"{count} Key{'' if count == 1 else 's'}")

        config = self._editor.configuration
        assert isinstance(config, PseudoregaliaConfiguration)

        with self._editor as editor:
            editor.set_configuration_field("required_keys", self.key_slider.value())

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, PseudoregaliaConfiguration)

        self.key_slider.setValue(preset.configuration.required_keys)
