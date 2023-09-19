from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.game_description import default_database
from randovania.games.game import RandovaniaGame
from randovania.gui.preset_settings.metroid_item_pool_tab import MetroidPresetItemPool
from randovania.gui.preset_settings.split_ammo_widget import SplitAmmoWidget

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class EchoesPresetItemPool(MetroidPresetItemPool):
    _split_ammo_widgets: list[SplitAmmoWidget]

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        pickup_database = default_database.pickup_database_for_game(self.game)

        self._create_split_ammo_widgets(pickup_database)

    def on_preset_changed(self, preset: Preset):
        super().on_preset_changed(preset)

        for split_ammo in self._split_ammo_widgets:
            split_ammo.on_preset_changed(preset, self._ammo_pickup_widgets)

    def _create_split_ammo_widgets(self, pickup_database: PickupDatabase):
        parent, layout, _ = self._boxes_for_category["beam"]

        self._split_ammo_widgets = []

        if self.game == RandovaniaGame.METROID_PRIME_ECHOES:
            beam_ammo = SplitAmmoWidget(
                parent,
                self._editor,
                unified_ammo=pickup_database.ammo_pickups["Beam Ammo Expansion"],
                split_ammo=[
                    pickup_database.ammo_pickups["Dark Ammo Expansion"],
                    pickup_database.ammo_pickups["Light Ammo Expansion"],
                ],
            )
            beam_ammo.setText("Split Beam Ammo Expansions")
            self._split_ammo_widgets.append(beam_ammo)

        if self._split_ammo_widgets:
            line = QtWidgets.QFrame(parent)
            line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
            layout.addWidget(line, layout.rowCount(), 0, 1, -1)

        for widget in self._split_ammo_widgets:
            layout.addWidget(widget, layout.rowCount(), 0, 1, -1)
