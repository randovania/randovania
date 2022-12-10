import randovania
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.preset_editor import PresetEditor


def dread_preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.games.dread.gui.preset_settings.dread_generation_tab import PresetDreadGeneration
    from randovania.games.dread.gui.preset_settings.dread_patches_tab import PresetDreadPatches
    from randovania.games.dread.gui.preset_settings.dread_item_pool_tab import DreadPresetItemPool
    from randovania.games.dread.gui.preset_settings.dread_energy_tab import PresetDreadEnergy
    from randovania.games.dread.gui.preset_settings.dread_goal_tab import PresetDreadGoal
    from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando

    return [
        PresetTrickLevel,
        *([
              PresetMetroidStartingArea,
          ] if window_manager.is_preview_mode else []),
        *([
              PresetDockRando,
          ] if randovania.is_dev_version() else []),
        PresetDreadGeneration,
        PresetLocationPool,
        PresetDreadGoal,
        DreadPresetItemPool,
        PresetDreadEnergy,
        PresetDreadPatches,
    ]
