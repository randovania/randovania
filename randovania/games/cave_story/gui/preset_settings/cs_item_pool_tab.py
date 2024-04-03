from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.cave_story.layout.cs_configuration import CSObjective
from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
from randovania.layout.base.standard_pickup_state import StandardPickupState

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class CSPresetItemPool(PresetItemPool):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.previousObj = CSObjective.NORMAL_ENDING

    def on_preset_changed(self, preset: Preset):
        super().on_preset_changed(preset)

        if self.previousObj != preset.configuration.objective:
            if self.previousObj == CSObjective.BAD_ENDING or preset.configuration.objective == CSObjective.BAD_ENDING:
                self._update_explosive(preset.configuration.objective == CSObjective.BAD_ENDING)
            self.previousObj = preset.configuration.objective

    def _update_explosive(self, bad_ending: bool):
        items = self._boxes_for_category["items"][2]
        explosive = next(item for item in items.keys() if item.name == "Explosive")
        explosive_box = items[explosive]

        if bad_ending:
            explosive_box.setVisible(False)
            explosive_box._update_for_state(StandardPickupState(True, 1, 0))
        else:
            explosive_box.setVisible(True)
            explosive_box._update_for_state(StandardPickupState(False, 1, 0))
