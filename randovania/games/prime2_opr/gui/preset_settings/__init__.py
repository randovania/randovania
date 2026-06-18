from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor


def preset_tabs(editor: PresetEditor, window_manager: WindowManager) -> list[type[PresetTab]]:
    from randovania.games.prime2.gui.preset_settings.echoes_beam_configuration_tab import PresetEchoesBeamConfiguration
    from randovania.games.prime2.gui.preset_settings.echoes_energy_tab import PresetEchoesEnergy
    from randovania.games.prime2.gui.preset_settings.echoes_goal_tab import PresetEchoesGoal
    from randovania.games.prime2.gui.preset_settings.echoes_starting_area import PresetEchoesStartingArea
    from randovania.games.prime2.gui.preset_settings.echoes_teleporters_tab import PresetTeleportersPrime2
    from randovania.games.prime2.gui.preset_settings.echoes_translators_tab import PresetEchoesTranslators
    from randovania.games.prime2_opr.gui.preset_settings.prime2_opr_patches_tab import PresetEchoesOPRPatches
    from randovania.games.prime2_opr.gui.preset_settings.prime2_opr_pickup_pool_tab import EchoesOPRPresetPickupPool
    from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando
    from randovania.gui.preset_settings.generation_tab import PresetGeneration
    from randovania.gui.preset_settings.hints_tab import PresetHints
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel

    return [
        PresetTrickLevel,
        PresetGeneration,
        PresetHints,
        PresetEchoesGoal,
        PresetLocationPool,
        EchoesOPRPresetPickupPool,
        PresetEchoesEnergy,
        PresetTeleportersPrime2,
        PresetEchoesStartingArea,
        PresetDockRando,
        PresetEchoesTranslators,
        PresetEchoesBeamConfiguration,
        PresetEchoesOPRPatches,
    ]
