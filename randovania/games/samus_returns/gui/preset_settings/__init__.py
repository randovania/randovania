from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor


def msr_preset_tabs(editor: PresetEditor, window_manager: WindowManager) -> list[type[PresetTab]]:
    from randovania.games.samus_returns.gui.preset_settings.msr_aeion_energy_tab import PresetMSRAeionAndEnergy
    from randovania.games.samus_returns.gui.preset_settings.msr_goal_tab import PresetMSRGoal
    from randovania.games.samus_returns.gui.preset_settings.msr_patches_tab import PresetMSRPatches
    from randovania.games.samus_returns.gui.preset_settings.msr_reserves_tab import PresetMSRReserves
    from randovania.games.samus_returns.gui.preset_settings.msr_starting_area import PresetMSRStartingArea
    from randovania.games.samus_returns.gui.preset_settings.msr_teleporters_tab import PresetTeleportersMSR
    from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando
    from randovania.gui.preset_settings.generation_tab import PresetGeneration
    from randovania.gui.preset_settings.hints_tab import PresetHints
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.metroid_pickup_pool_tab import MetroidPresetPickupPool
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel

    return [
        PresetTrickLevel,
        PresetGeneration,
        PresetMSRGoal,
        PresetHints,
        PresetLocationPool,
        MetroidPresetPickupPool,
        PresetMSRStartingArea,
        PresetTeleportersMSR,
        PresetDockRando,
        PresetMSRAeionAndEnergy,
        PresetMSRReserves,
        PresetMSRPatches,
    ]
