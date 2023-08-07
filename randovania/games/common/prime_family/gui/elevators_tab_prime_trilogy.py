from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.common.gui.elevators_tab_common import PresetElevatorsCommon
from randovania.gui.lib import signal_handling

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.games.common.prime_family.layout.lib.prime_triology_teleporters import (
        PrimeTriologyTeleporterConfiguration,
    )
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetElevatorsPrimeTrilogy(PresetElevatorsCommon):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        signal_handling.on_checked(self.skip_final_bosses_check, self._update_require_final_bosses)

    def on_preset_changed(self, preset: Preset):
        super().on_preset_changed(preset)
        config = preset.configuration
        config_elevators: PrimeTriologyTeleporterConfiguration = config.elevators
        self.skip_final_bosses_check.setChecked(config_elevators.skip_final_bosses)
