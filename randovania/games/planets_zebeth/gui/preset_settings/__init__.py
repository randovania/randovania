from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.gui.preset_settings.starting_area_tab import PresetStartingArea

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor


def preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    from randovania.games.planets_zebeth.gui.preset_settings.metroid_patches_tab import PresetMetroidPatches
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.metroid_item_pool_tab import MetroidPresetItemPool
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel

    return [PresetTrickLevel, PresetLocationPool, MetroidPresetItemPool, PresetMetroidPatches, PresetStartingArea]
