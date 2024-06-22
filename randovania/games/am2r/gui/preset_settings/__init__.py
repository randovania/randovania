from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor


def preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    from randovania.games.am2r.gui.preset_settings.am2r_chaos_tab import PresetAM2RChaos
    from randovania.games.am2r.gui.preset_settings.am2r_goal_tab import PresetAM2RGoal
    from randovania.games.am2r.gui.preset_settings.am2r_hints_tab import PresetAM2RHints
    from randovania.games.am2r.gui.preset_settings.am2r_patches_tab import PresetAM2RPatches
    from randovania.games.am2r.gui.preset_settings.am2r_teleporters_tab import PresetTeleportersAM2R
    from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando
    from randovania.gui.preset_settings.generation_tab import PresetGeneration
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.metroid_item_pool_tab import MetroidPresetItemPool
    from randovania.gui.preset_settings.patcher_energy_tab import PresetPatcherEnergy
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel

    return [
        PresetTrickLevel,
        PresetGeneration,
        PresetAM2RHints,
        PresetLocationPool,
        PresetAM2RGoal,
        MetroidPresetItemPool,
        PresetPatcherEnergy,
        PresetMetroidStartingArea,
        PresetDockRando,
        PresetTeleportersAM2R,
        PresetAM2RPatches,
        PresetAM2RChaos,
    ]
