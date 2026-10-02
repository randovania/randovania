from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor


def preset_tabs(editor: PresetEditor, window_manager: WindowManager) -> list[type[PresetTab]]:
    from randovania.games.yokus_island_express.gui.preset_settings.yokus_island_express_patches_tab import (
        PresetYokuPatches,
    )
    from randovania.gui.preset_settings.dock_weakness_distributor_tab import PresetDockWeaknessDistributor
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.pickup_pool_tab import PresetPickupPool

    return [
        PresetLocationPool,
        PresetPickupPool,
        PresetYokuPatches,
        *PresetDockWeaknessDistributor.subclass_for_compatible_dock_types(editor.game),
    ]
