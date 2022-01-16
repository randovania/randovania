from randovania.game_description import default_database
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.preset_editor import PresetEditor


def prime2_preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    game_enum = editor.game
    game_description = default_database.game_description_for(game_enum)

    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.gui.preset_settings.patcher_energy_tab import PresetPatcherEnergy
    from randovania.gui.preset_settings.elevators_tab import PresetElevators
    from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea
    from randovania.gui.preset_settings.generation_tab import PresetGeneration
    from randovania.games.prime2.gui.preset_settings.echoes_goal_tab import PresetEchoesGoal
    from randovania.games.prime2.gui.preset_settings.echoes_hints_tab import PresetEchoesHints
    from randovania.games.prime2.gui.preset_settings.echoes_translators_tab import PresetEchoesTranslators
    from randovania.games.prime2.gui.preset_settings.echoes_beam_configuration_tab import PresetEchoesBeamConfiguration
    from randovania.games.prime2.gui.preset_settings.echoes_patches_tab import PresetEchoesPatches
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.games.prime2.gui.preset_settings.echoes_item_pool_tab import EchoesPresetItemPool
    return [
        PresetTrickLevel(editor, game_description, window_manager),
        PresetPatcherEnergy(editor, game_enum),
        PresetElevators(editor, game_description),
        PresetMetroidStartingArea(editor, game_description),
        PresetGeneration(editor, game_description),
        PresetEchoesGoal(editor),
        PresetEchoesHints(editor),
        PresetEchoesTranslators(editor),
        PresetEchoesBeamConfiguration(editor),
        PresetEchoesPatches(editor),
        PresetLocationPool(editor, game_description),
        EchoesPresetItemPool(editor),
    ]
