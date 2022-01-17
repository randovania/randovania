from randovania.game_description import default_database

from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.preset_editor import PresetEditor


def cs_preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    game_enum = editor.game
    game_description = default_database.game_description_for(game_enum)

    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.games.cave_story.gui.preset_settings.cs_starting_area_tab import PresetCSStartingArea
    from randovania.games.cave_story.gui.preset_settings.cs_generation_tab import PresetCSGeneration
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.games.cave_story.gui.preset_settings.cs_item_pool_tab import CSPresetItemPool
    from randovania.games.cave_story.gui.preset_settings.cs_goal_tab import PresetCSObjective
    from randovania.games.cave_story.gui.preset_settings.cs_hp_tab import PresetCSHP

    return [
        PresetTrickLevel(editor, game_description, window_manager),
        PresetCSStartingArea(editor, game_description),
        PresetCSGeneration(editor, game_description),
        PresetCSObjective(editor),
        PresetLocationPool(editor, game_description),
        CSPresetItemPool(editor),
        PresetCSHP(editor)
    ]
