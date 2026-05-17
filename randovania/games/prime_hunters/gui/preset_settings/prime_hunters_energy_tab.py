from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime_hunters.gui.generated.preset_prime_hunters_energy_ui import Ui_PresetHuntersEnergy
from randovania.games.prime_hunters.layout.prime_hunters_configuration import HuntersConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetHuntersEnergy(PresetTab, Ui_PresetHuntersEnergy):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.energy_capacity_spin_box.valueChanged.connect(self._persist_capacity)

    @classmethod
    def tab_title(cls) -> str:
        return "Energy"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, HuntersConfiguration)
        self.energy_capacity_spin_box.setValue(config.starting_energy)

    def _persist_capacity(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("starting_energy", int(self.energy_capacity_spin_box.value()))
