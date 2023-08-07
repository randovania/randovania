from __future__ import annotations

from randovania.games.common.prime_family.gui.elevators_tab_prime_trilogy import PresetElevatorsPrimeTrilogy
from randovania.gui.generated.preset_elevators_prime1_ui import Ui_PresetElevatorsPrime1
from randovania.layout.lib.teleporters import (
    TeleporterShuffleMode,
)
from randovania.lib import enum_lib


class PresetElevatorsPrime1(PresetElevatorsPrimeTrilogy, Ui_PresetElevatorsPrime1):
    compatible_modes = [
        value for value in enum_lib.iterate_enum(TeleporterShuffleMode)
        if value != TeleporterShuffleMode.ECHOES_SHUFFLED
    ]

