
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.preset_editor import PresetEditor
from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea


def preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.metroid_item_pool_tab import MetroidPresetItemPool
    from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando
    from randovania.games.am2r.gui.preset_settings.am2r_patches_tab import PresetAM2RPatches

    return [
        PresetTrickLevel,
        PresetLocationPool,
        MetroidPresetItemPool,
        PresetAM2RPatches,
        PresetDockRando,
        PresetMetroidStartingArea
    ]
