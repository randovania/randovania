from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor


def preset_tabs(editor: PresetEditor, window_manager: WindowManager) -> list[type[PresetTab]]:
    from randovania.games.factorio.gui.preset_settings.factorio_patches_tab import PresetFactorioPatches
    from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool

    return [
        PresetItemPool,
        PresetLocationPool,
        PresetFactorioPatches,
    ]
