from randovania.game_description import default_database
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.preset_editor import PresetEditor


def super_metroid_preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    game_enum = editor.game
    game_description = default_database.game_description_for(game_enum)
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea
    from randovania.gui.preset_settings.generation_tab import PresetGeneration
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.metroid_item_pool_tab import MetroidPresetItemPool
    from randovania.games.super_metroid.gui.preset_settings.super_patches_tab import PresetSuperPatchConfiguration

    itemPoolTab = MetroidPresetItemPool(editor)
    itemPoolTab.pickup_style_widget.hide()

    return [
        PresetTrickLevel(editor, game_description, window_manager),
        PresetMetroidStartingArea(editor, game_description),
        PresetGeneration(editor, game_description),
        PresetLocationPool(editor, game_description),
        itemPoolTab,
        PresetSuperPatchConfiguration(editor),
    ]
