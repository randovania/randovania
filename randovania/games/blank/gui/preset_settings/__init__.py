from randovania.game_description import default_database

from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.preset_editor import PresetEditor


def preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
    from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando
    from randovania.games.blank.gui.preset_settings.blank_patches_tab import PresetBlankPatches

    return [
        PresetTrickLevel,
        PresetLocationPool,
        PresetItemPool,
        PresetBlankPatches,
        PresetDockRando,
    ]
