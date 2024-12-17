from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.cave_story.gui.generated.preset_cs_hp_ui import Ui_PresetCSHP
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetCSHP(PresetTab, Ui_PresetCSHP):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.starting_hp_spin_box.valueChanged.connect(self._on_starting_hp_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "HP"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _on_starting_hp_changed(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("starting_hp", int(self.starting_hp_spin_box.value()))

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, CSConfiguration)
        self.starting_hp_spin_box.setValue(preset.configuration.starting_hp)
