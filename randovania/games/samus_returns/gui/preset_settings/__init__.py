from randovania.game_description import default_database

from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.preset_editor import PresetEditor


def preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
    from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando
    from randovania.games.samus_returns.gui.preset_settings.msr_patches_tab import PresetMSRPatches
    # from randovania.games.samus_returns.gui.preset_settings.msr_generation_tab import PresetMSRGeneration
    # from randovania.games.samus_returns.gui.preset_settings.msr_item_pool_tab import MSRPresetItemPool
    # from randovania.games.samus_returns.gui.preset_settings.msr_energy_tab import PresetMSREnergy
    # from randovania.games.samus_returns.gui.preset_settings.msr_goal_tab import PresetMSRGoal

    return [
        PresetTrickLevel,
        PresetMetroidStartingArea,
        PresetLocationPool,
        PresetItemPool,
        PresetMSRPatches,
        PresetDockRando,
    ]
