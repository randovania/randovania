from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor


def prime1_preset_tabs(editor: PresetEditor, window_manager: WindowManager) -> list[type[PresetTab]]:
    from randovania.games.prime1.gui.preset_settings.prime_dock_rando_tab import PresetPrimeDockRando
    from randovania.games.prime1.gui.preset_settings.prime_enemy_stat_randomizer import PresetEnemyAttributeRandomizer
    from randovania.games.prime1.gui.preset_settings.prime_generation_tab import PresetPrimeGeneration
    from randovania.games.prime1.gui.preset_settings.prime_goal_tab import PresetPrimeGoal
    from randovania.games.prime1.gui.preset_settings.prime_patches_chaos import PresetPrimeChaos
    from randovania.games.prime1.gui.preset_settings.prime_patches_qol import PresetPrimeQol
    from randovania.games.prime1.gui.preset_settings.prime_teleporters_tab import PresetTeleportersPrime1
    from randovania.gui.preset_settings.hints_tab import PresetHints
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.metroid_item_pool_tab import MetroidPresetItemPool
    from randovania.gui.preset_settings.patcher_energy_tab import PresetPatcherEnergy
    from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel

    return [
        PresetTrickLevel,
        PresetPrimeGeneration,
        PresetPrimeGoal,
        PresetHints,
        PresetLocationPool,
        MetroidPresetItemPool,
        PresetPatcherEnergy,
        PresetTeleportersPrime1,
        PresetMetroidStartingArea,
        PresetPrimeDockRando,
        PresetPrimeQol,
        PresetEnemyAttributeRandomizer,
        PresetPrimeChaos,
    ]
