import dataclasses
import functools

from PySide6 import QtWidgets

from randovania.game_description import default_database
from randovania.game_description.item.major_item import MajorItem
from randovania.gui.lib.scroll_protected import ScrollProtectedSpinBox
from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
from randovania.gui.preset_settings.pickup_style_widget import PickupStyleWidget
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.major_item_state import DEFAULT_MAXIMUM_SHUFFLED
from randovania.layout.preset import Preset


class DreadPresetItemPool(PresetItemPool):
    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        item_database = default_database.item_database_for_game(self.game)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)

        self._energy_item_to_starting_spinbox = {}
        self._energy_item_to_shuffled_spinbox = {}
        self._energy_tank_item = item_database.major_items["Energy Tank"]
        self._energy_part_item = item_database.major_items["Energy Part"]
        self._create_energy_box()
        self._create_pickup_style_box(size_policy)

    def on_preset_changed(self, preset: Preset):
        super().on_preset_changed(preset)
        layout = preset.configuration
        major_configuration = layout.major_items_configuration

        self.pickup_style_widget.update(layout)

        # Energy Tank
        for item in [self._energy_tank_item, self._energy_part_item]:
            state = major_configuration.items_state[item]
            self._energy_item_to_starting_spinbox[item].setValue(state.num_included_in_starting_items)
            self._energy_item_to_shuffled_spinbox[item].setValue(state.num_shuffled_pickups)

    def _create_pickup_style_box(self, size_policy):
        self.pickup_style_widget = PickupStyleWidget(None, self._editor)
        self.item_pool_layout.insertWidget(1, self.pickup_style_widget)
        # widget.Changed.connect(partial(self._on_major_item_updated, widget))

    def _create_energy_box(self):
        category_box, category_layout, _ = self._boxes_for_category["energy_tank"]
        game_description = default_database.game_description_for(self.game)

        row = 0
        for item in [self._energy_tank_item, self._energy_part_item]:
            resource = game_description.resource_database.get_item(item.progression[0])

            starting_label = QtWidgets.QLabel(category_box)
            starting_label.setText(f"Starting {item.name}")
            category_layout.addWidget(starting_label, row, 0)

            spinbox = self._energy_item_to_starting_spinbox[item] = ScrollProtectedSpinBox(category_box)
            spinbox.setMaximum(resource.max_capacity)
            spinbox.valueChanged.connect(functools.partial(self._on_update_starting, item=item))
            category_layout.addWidget(spinbox, row, 1)

            row += 1

            shuffled_label = QtWidgets.QLabel(category_box)
            shuffled_label.setText(f"Shuffled {item.name}")
            category_layout.addWidget(shuffled_label, row, 0)

            spinbox = self._energy_item_to_shuffled_spinbox[item] = ScrollProtectedSpinBox(category_box)
            spinbox.setMaximum(DEFAULT_MAXIMUM_SHUFFLED[-1])
            spinbox.valueChanged.connect(functools.partial(self._on_update_shuffled, item=item))
            category_layout.addWidget(spinbox, row, 1)

            row += 1

    def _on_update_starting(self, value: int, item: MajorItem):
        with self._editor as options:
            major_configuration = options.major_items_configuration
            options.major_items_configuration = major_configuration.replace_state_for_item(
                item,
                dataclasses.replace(major_configuration.items_state[item],
                                    num_included_in_starting_items=value)
            )

    def _on_update_shuffled(self, value: int, item: MajorItem):
        with self._editor as options:
            major_configuration = options.major_items_configuration
            options.major_items_configuration = major_configuration.replace_state_for_item(
                item,
                dataclasses.replace(major_configuration.items_state[item],
                                    num_shuffled_pickups=value)
            )
