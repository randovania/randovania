from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox

from randovania.game_description.game_description import GameDescription
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.metroid_pickup_pool_tab import MetroidPresetPickupPool
from randovania.interface_common.preset_editor import PresetEditor


class PlanetsZebethPresetPickupPool(MetroidPresetPickupPool):
    ammo_widgets: list[QCheckBox] = []

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)

        for ammo_def, ammo_widget in self._ammo_pickup_widgets.items():
            if ammo_def.name.endswith("Missile Tank"):
                if ammo_widget.require_main_item_check is not None:
                    ammo_widget.require_main_item_check.stateChanged.connect(self.on_required_missiles_changed)
                    self.ammo_widgets.append(ammo_widget.require_main_item_check)

    def on_required_missiles_changed(self, state: int) -> None:
        for ammo_widget in self.ammo_widgets:
            ammo_widget.setChecked(state == Qt.CheckState.Checked.value)
