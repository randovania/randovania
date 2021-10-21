from typing import List

from PySide2 import QtWidgets

from randovania.game_description import default_database
from randovania.game_description.item.item_database import ItemDatabase
from randovania.games.game import RandovaniaGame
from randovania.gui.preset_settings.metroid_item_pool_tab import MetroidPresetItemPool
from randovania.gui.preset_settings.split_ammo_widget import SplitAmmoWidget
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class EchoesPresetItemPool(MetroidPresetItemPool):
    _split_ammo_widgets: List[SplitAmmoWidget]

    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        item_database = default_database.item_database_for_game(self.game)

        self._create_split_ammo_widgets(item_database)

    def on_preset_changed(self, preset: Preset):
        super().on_preset_changed(preset)

        for split_ammo in self._split_ammo_widgets:
            split_ammo.on_preset_changed(preset, self._ammo_pickup_widgets)

    def _create_split_ammo_widgets(self, item_database: ItemDatabase):
        parent, layout, _ = self._boxes_for_category["beam"]

        self._split_ammo_widgets = []

        if self.game == RandovaniaGame.METROID_PRIME_ECHOES:
            beam_ammo = SplitAmmoWidget(
                parent, self._editor,
                unified_ammo=item_database.ammo["Beam Ammo Expansion"],
                split_ammo=[
                    item_database.ammo["Dark Ammo Expansion"],
                    item_database.ammo["Light Ammo Expansion"],
                ],
            )
            beam_ammo.setText("Split Beam Ammo Expansions")
            self._split_ammo_widgets.append(beam_ammo)

        if self._split_ammo_widgets:
            line = QtWidgets.QFrame(parent)
            line.setFrameShape(QtWidgets.QFrame.HLine)
            line.setFrameShadow(QtWidgets.QFrame.Sunken)
            layout.addWidget(line, layout.rowCount(), 0, 1, -1)

        for widget in self._split_ammo_widgets:
            layout.addWidget(widget, layout.rowCount(), 0, 1, -1)
