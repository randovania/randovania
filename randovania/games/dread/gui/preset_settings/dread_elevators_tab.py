from __future__ import annotations

from randovania.games.common.gui.elevators_tab_common import PresetElevatorsCommon
from randovania.gui.generated.preset_elevators_dread_ui import Ui_PresetElevatorsDread
from randovania.layout.lib.teleporters import (
    TeleporterShuffleMode,
)


class PresetElevatorsDread(PresetElevatorsCommon, Ui_PresetElevatorsDread):
    compatible_modes = [
        TeleporterShuffleMode.VANILLA,
        TeleporterShuffleMode.TWO_WAY_RANDOMIZED,
        TeleporterShuffleMode.TWO_WAY_UNCHECKED,
        TeleporterShuffleMode.ONE_WAY_ELEVATOR,
        TeleporterShuffleMode.ONE_WAY_ELEVATOR_REPLACEMENT,
    ]
