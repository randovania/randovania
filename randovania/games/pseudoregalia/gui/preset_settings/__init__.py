from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.pseudoregalia.gui.preset_settings.pseudoregalia_goal_tab import PresetPseudoregaliaGoal
from randovania.games.pseudoregalia.gui.preset_settings.pseudoregalia_item_pool_tab import PseudoregaliaPresetItemPool
from randovania.gui.preset_settings.starting_area_tab import PresetStartingArea

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor


def preset_tabs(editor: PresetEditor, window_manager: WindowManager) -> list[type[PresetTab]]:
    from randovania.games.pseudoregalia.gui.preset_settings.pseudoregalia_other_tab import PresetPseudoregaliaOther
    from randovania.gui.preset_settings.generation_tab import PresetGeneration
    from randovania.gui.preset_settings.hints_tab import PresetHints
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel

    return [
        PresetTrickLevel,
        PresetGeneration,
        PresetHints,
        PresetLocationPool,
        PresetPseudoregaliaGoal,
        PseudoregaliaPresetItemPool,
        PresetPseudoregaliaOther,
        PresetStartingArea,
    ]
