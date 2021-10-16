import dataclasses
from typing import List

from PySide2 import QtWidgets

from randovania.game_description import default_database
from randovania.game_description.item.item_database import ItemDatabase
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.games.game import RandovaniaGame
from randovania.gui.lib import signal_handling
from randovania.gui.lib.scroll_protected import ScrollProtectedSpinBox
from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
from randovania.gui.preset_settings.pickup_style_widget import PickupStyleWidget
from randovania.gui.preset_settings.progressive_item_widget import ProgressiveItemWidget
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.major_item_state import DEFAULT_MAXIMUM_SHUFFLED
from randovania.layout.preset import Preset


class MetroidPresetItemPool(PresetItemPool):
    _progressive_widgets: List[ProgressiveItemWidget]

    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        item_database = default_database.item_database_for_game(self.game)
        game_description = default_database.game_description_for(self.game)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)

        self._energy_tank_item = item_database.major_items["Energy Tank"]
        self._create_energy_tank_box(game_description.resource_database.energy_tank)
        self._create_progressive_widgets(item_database)
        self._create_pickup_style_box(size_policy)
        signal_handling.on_checked(self.multi_pickup_placement_check, self._persist_multi_pickup_placement)

    def on_preset_changed(self, preset: Preset):
        super().on_preset_changed(preset)
        layout = preset.configuration
        major_configuration = layout.major_items_configuration

        for progressive_widget in self._progressive_widgets:
            progressive_widget.on_preset_changed(
                preset,
                self._boxes_for_category[progressive_widget.progressive_item.item_category.name][2],
            )

        self.pickup_style_widget.update(layout)

        # Energy Tank
        energy_tank_state = major_configuration.items_state[self._energy_tank_item]
        self.energy_tank_starting_spinbox.setValue(energy_tank_state.num_included_in_starting_items)
        self.energy_tank_shuffled_spinbox.setValue(energy_tank_state.num_shuffled_pickups)

    def _persist_multi_pickup_placement(self, value: bool):
        with self._editor as editor:
            editor.set_configuration_field("multi_pickup_placement", value)

    def _create_pickup_style_box(self, size_policy):
        self.pickup_style_widget = PickupStyleWidget(None, self._editor)
        self.item_pool_layout.insertWidget(1, self.pickup_style_widget)
        # widget.Changed.connect(partial(self._on_major_item_updated, widget))

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
            major_configuration = options.major_items_configuration
            options.major_items_configuration = major_configuration.replace_state_for_item(
                self._energy_tank_item,
                dataclasses.replace(major_configuration.items_state[self._energy_tank_item],
                                    num_included_in_starting_items=value)
            )

    def _on_update_shuffled_energy_tank(self, value: int):
        with self._editor as options:
            major_configuration = options.major_items_configuration
            options.major_items_configuration = major_configuration.replace_state_for_item(
                self._energy_tank_item,
                dataclasses.replace(major_configuration.items_state[self._energy_tank_item],
                                    num_shuffled_pickups=value)
            )

    def _create_progressive_widgets(self, item_database: ItemDatabase):
        self._progressive_widgets = []

        all_progressive = []

        if self.game == RandovaniaGame.METROID_PRIME_ECHOES:
            all_progressive.append((
                "Progressive Suit",
                ("Dark Suit", "Light Suit"),
            ))
            all_progressive.append((
                "Progressive Grapple",
                ("Grapple Beam", "Screw Attack"),
            ))
        elif self.game == RandovaniaGame.METROID_PRIME_CORRUPTION:
            all_progressive.append((
                "Progressive Missile",
                ("Ice Missile", "Seeker Missile"),
            ))
            all_progressive.append((
                "Progressive Beam",
                ("Plasma Beam", "Nova Beam"),
            ))

        for (progressive_item_name, non_progressive_items) in all_progressive:
            progressive_item = item_database.major_items[progressive_item_name]
            parent, layout, _ = self._boxes_for_category[progressive_item.item_category.name]

            widget = ProgressiveItemWidget(
                parent, self._editor,
                progressive_item=progressive_item,
                non_progressive_items=[item_database.major_items[it] for it in non_progressive_items],
            )
            widget.setText("Use progressive {}".format(" → ".join(non_progressive_items)))
            self._progressive_widgets.append(widget)
            layout.addWidget(widget)
