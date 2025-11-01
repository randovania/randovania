from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor


def cs_preset_tabs(editor: PresetEditor, window_manager: WindowManager) -> list[type[PresetTab]]:
    from randovania.games.cave_story.gui.preset_settings.cs_generation_tab import PresetCSGeneration
    from randovania.games.cave_story.gui.preset_settings.cs_goal_tab import PresetCSObjective
    from randovania.games.cave_story.gui.preset_settings.cs_hp_tab import PresetCSHP
    from randovania.games.cave_story.gui.preset_settings.cs_pickup_pool_tab import CSPresetPickupPool
    from randovania.games.cave_story.gui.preset_settings.cs_starting_area_tab import PresetCSStartingArea
    from randovania.gui.preset_settings.hints_tab import PresetHints
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel

    return [
        PresetTrickLevel,
        PresetCSGeneration,
        PresetHints,
        PresetCSObjective,
        PresetLocationPool,
        CSPresetPickupPool,
        PresetCSStartingArea,
        PresetCSHP,
    ]
