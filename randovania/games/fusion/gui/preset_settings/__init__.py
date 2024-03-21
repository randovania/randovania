from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.gui.preset_settings.starting_area_tab import PresetStartingArea

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor


def preset_tabs(editor: PresetEditor, window_manager: WindowManager) -> list[type[PresetTab]]:
    from randovania.games.fusion.gui.preset_settings.fusion_goal_tab import PresetFusionGoal
    from randovania.games.fusion.gui.preset_settings.fusion_hints_tab import PresetFusionHints
    from randovania.games.fusion.gui.preset_settings.fusion_patches_tab import PresetFusionPatches
    from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando
    from randovania.gui.preset_settings.generation_tab import PresetGeneration
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.metroid_item_pool_tab import MetroidPresetItemPool
    from randovania.gui.preset_settings.patcher_energy_tab import PresetPatcherEnergy
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel

    return [
        PresetTrickLevel,
        PresetGeneration,
        PresetFusionGoal,
        PresetFusionHints,
        PresetLocationPool,
        MetroidPresetItemPool,
        PresetPatcherEnergy,
        PresetStartingArea,
        PresetDockRando,
        PresetFusionPatches,
    ]
