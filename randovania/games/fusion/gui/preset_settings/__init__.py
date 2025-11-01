from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor


def preset_tabs(editor: PresetEditor, window_manager: WindowManager) -> list[type[PresetTab]]:
    from randovania.games.fusion.gui.preset_settings.fusion_dock_tab import PresetFusionDocks
    from randovania.games.fusion.gui.preset_settings.fusion_goal_tab import PresetFusionGoal
    from randovania.games.fusion.gui.preset_settings.fusion_patches_tab import PresetFusionPatches
    from randovania.gui.preset_settings.generation_tab import PresetGeneration
    from randovania.gui.preset_settings.hints_tab import PresetHints
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.metroid_pickup_pool_tab import MetroidPresetPickupPool
    from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel

    tabs = [
        PresetTrickLevel,
        PresetGeneration,
        PresetHints,
        PresetFusionGoal,
        PresetLocationPool,
        MetroidPresetPickupPool,
        PresetFusionPatches,
        PresetMetroidStartingArea,
        PresetFusionDocks,
    ]

    return tabs
