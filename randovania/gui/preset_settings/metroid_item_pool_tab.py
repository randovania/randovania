from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.game_description import default_database
from randovania.gui.lib.scroll_protected import ScrollProtectedSpinBox
from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
from randovania.gui.preset_settings.pickup_style_widget import PickupStyleWidget
from randovania.layout.base.standard_pickup_state import DEFAULT_MAXIMUM_SHUFFLED

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class MetroidPresetItemPool(PresetItemPool):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        pickup_database = default_database.pickup_database_for_game(self.game)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)

        self._energy_tank_item = pickup_database.standard_pickups["Energy Tank"]
        self._create_energy_tank_box(game_description.resource_database.energy_tank)
        self._create_pickup_style_box(size_policy)

    def on_preset_changed(self, preset: Preset):
        super().on_preset_changed(preset)
        layout = preset.configuration
        major_configuration = layout.standard_pickup_configuration

        self.pickup_style_widget.update(layout)

        # Energy Tank
        energy_tank_state = major_configuration.pickups_state[self._energy_tank_item]
        self.energy_tank_starting_spinbox.setValue(energy_tank_state.num_included_in_starting_pickups)
        self.energy_tank_shuffled_spinbox.setValue(energy_tank_state.num_shuffled_pickups)

    def _create_pickup_style_box(self, size_policy):
        self.pickup_style_widget = PickupStyleWidget(None, self._editor)
        self.item_pool_layout.insertWidget(1, self.pickup_style_widget)

    def _create_energy_tank_box(self, energy_tank_resource: ItemResourceInfo):
        category_box, category_layout, _ = self._boxes_for_category["energy_tank"]

        starting_label = QtWidgets.QLabel(category_box)
        starting_label.setText("Starting Quantity")
        category_layout.addWidget(starting_label, 0, 0)

        self.energy_tank_starting_spinbox = ScrollProtectedSpinBox(category_box)
        self.energy_tank_starting_spinbox.setMaximum(energy_tank_resource.max_capacity)
        self.energy_tank_starting_spinbox.valueChanged.connect(self._on_update_starting_energy_tank)
        category_layout.addWidget(self.energy_tank_starting_spinbox, 0, 1)

        shuffled_label = QtWidgets.QLabel(category_box)
        shuffled_label.setText("Shuffled Quantity")
        category_layout.addWidget(shuffled_label, 1, 0)

        self.energy_tank_shuffled_spinbox = ScrollProtectedSpinBox(category_box)
        self.energy_tank_shuffled_spinbox.setMaximum(DEFAULT_MAXIMUM_SHUFFLED[-1])
        self.energy_tank_shuffled_spinbox.valueChanged.connect(self._on_update_shuffled_energy_tank)
        category_layout.addWidget(self.energy_tank_shuffled_spinbox, 1, 1)

    def _on_update_starting_energy_tank(self, value: int):
        with self._editor as options:
            major_configuration = options.standard_pickup_configuration
            options.standard_pickup_configuration = major_configuration.replace_state_for_pickup(
                self._energy_tank_item,
                dataclasses.replace(
                    major_configuration.pickups_state[self._energy_tank_item], num_included_in_starting_pickups=value
                ),
            )

    def _on_update_shuffled_energy_tank(self, value: int):
        with self._editor as options:
            major_configuration = options.standard_pickup_configuration
            options.standard_pickup_configuration = major_configuration.replace_state_for_pickup(
                self._energy_tank_item,
                dataclasses.replace(
                    major_configuration.pickups_state[self._energy_tank_item], num_shuffled_pickups=value
                ),
            )
