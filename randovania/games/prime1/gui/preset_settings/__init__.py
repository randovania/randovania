from randovania.game_description import default_database

from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.preset_editor import PresetEditor


def prime1_preset_tabs(editor: PresetEditor, window_manager: WindowManager):

    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.gui.preset_settings.patcher_energy_tab import PresetPatcherEnergy
    from randovania.gui.preset_settings.elevators_tab import PresetElevators
    from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea
    from randovania.games.prime1.gui.preset_settings.prime_goal_tab import PresetPrimeGoal
    from randovania.games.prime1.gui.preset_settings.prime_hints_tab import PresetPrimeHints
    from randovania.games.prime1.gui.preset_settings.prime_patches_tab import PresetPrimePatches
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.metroid_item_pool_tab import MetroidPresetItemPool
    from randovania.games.prime1.gui.preset_settings.prime_generation_tab import PresetPrimeGeneration
    from randovania.games.prime1.gui.preset_settings.prime_enemy_stat_randomizer import PresetEnemyAttributeRandomizer
    from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando
    return [
        PresetTrickLevel,
        PresetPatcherEnergy,
        PresetElevators,
        PresetMetroidStartingArea,
        PresetPrimeGeneration,
        PresetPrimeGoal,
        PresetPrimeHints,
        PresetDockRando,
        PresetEnemyAttributeRandomizer,
        PresetPrimePatches,
        PresetLocationPool,
        MetroidPresetItemPool,
    ]
