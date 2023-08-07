from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.common.prime_family.gui.elevators_tab_prime_trilogy import PresetElevatorsPrimeTrilogy
from randovania.games.prime2.exporter.patch_data_factory import should_keep_elevator_sounds
from randovania.gui.generated.preset_elevators_prime2_ui import Ui_PresetElevatorsPrime2
from randovania.gui.lib import signal_handling
from randovania.layout.lib.teleporters import (
    TeleporterShuffleMode,
)
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.games.common.prime_family.layout.lib.prime_triology_teleporters import (
        PrimeTriologyTeleporterConfiguration,
    )
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetElevatorsPrime2(PresetElevatorsPrimeTrilogy, Ui_PresetElevatorsPrime2):
    compatible_modes = list(enum_lib.iterate_enum(TeleporterShuffleMode))
    custom_weights = {
            "Great Temple": 0,
            "Agon Wastes": 1,
            "Torvus Bog": 2,
            "Sanctuary Fortress": 3,
            "Temple Grounds": 5,
        }

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        signal_handling.on_checked(self.elevators_allow_unvisited_names_check, self._update_allow_unvisited_names)

    def on_preset_changed(self, preset: Preset):
        super().on_preset_changed(preset)
        config = preset.configuration
        config_elevators: PrimeTriologyTeleporterConfiguration = config.elevators
        sound_bug_warning = False
        sound_bug_warning = not should_keep_elevator_sounds(config)
        self.elevators_allow_unvisited_names_check.setChecked(config_elevators.allow_unvisited_room_names)
        self.elevators_help_sound_bug_label.setVisible(sound_bug_warning)
