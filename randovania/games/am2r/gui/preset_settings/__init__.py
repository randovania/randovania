from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea

if TYPE_CHECKING:
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor


def preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    from randovania.games.am2r.gui.preset_settings.am2r_chaos_tab import PresetAM2RChaos
    from randovania.games.am2r.gui.preset_settings.am2r_dock_tab import PresetAM2RDoors
    from randovania.games.am2r.gui.preset_settings.am2r_gameplay_tab import PresetAM2RGameplay
    from randovania.games.am2r.gui.preset_settings.am2r_goal_tab import PresetAM2RGoal
    from randovania.games.am2r.gui.preset_settings.am2r_hints_tab import PresetAM2RHints
    from randovania.games.am2r.gui.preset_settings.am2r_room_design_tab import PresetAM2RRoomDesign
    from randovania.games.am2r.gui.preset_settings.am2r_teleporters_tab import PresetTeleportersAM2R
    from randovania.gui.preset_settings.generation_tab import PresetGeneration
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.metroid_item_pool_tab import MetroidPresetItemPool
    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel

    return [
        PresetTrickLevel,
        PresetGeneration,
        PresetAM2RHints,
        PresetLocationPool,
        PresetAM2RGoal,
        MetroidPresetItemPool,
        PresetMetroidStartingArea,
        PresetAM2RDoors,
        PresetTeleportersAM2R,
        PresetAM2RGameplay,
        PresetAM2RRoomDesign,
        PresetAM2RChaos,
    ]
