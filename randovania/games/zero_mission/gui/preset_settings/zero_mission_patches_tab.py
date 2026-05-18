from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.zero_mission.gui.generated.preset_zero_mission_patches_ui import Ui_PresetMZMPatches
from randovania.games.zero_mission.layout import MZMConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetMZMPatches(PresetTab, Ui_PresetMZMPatches):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.setCentralWidget(self.root_widget)

        # Signals
        self.etank_capacity_spin_box.valueChanged.connect(self._persist_tank_capacity)

    @classmethod
    def tab_title(cls) -> str:
        return "Gameplay"

    @classmethod
    def header_name(cls) -> str | None:
        return cls.GAME_MODIFICATIONS_HEADER

    def _persist_tank_capacity(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("energy_per_tank", int(self.etank_capacity_spin_box.value()))

    def on_preset_changed(self, preset: Preset[MZMConfiguration]) -> None:
        config = preset.configuration
        assert isinstance(config, MZMConfiguration)
        self.etank_capacity_spin_box.setValue(config.energy_per_tank)
