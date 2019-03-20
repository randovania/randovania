from functools import partial
from pathlib import Path
from typing import List

from PySide2 import QtCore
from PySide2.QtWidgets import QMainWindow, QRadioButton, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from randovania.game_description.default_database import default_prime2_game_description
from randovania.game_description.node import PickupNode
from randovania.gui.common_qt_lib import set_default_window_icon
from randovania.gui.seed_details_window_ui import Ui_SeedDetailsWindow
from randovania.layout.layout_description import LayoutDescription


def _unique(iterable):
    seen = set()

    for item in iterable:
        if item in seen:
            continue
        seen.add(item)
        yield item


def _show_pickup_spoiler(button):
    button.setText(button.item_name)
    button.item_is_hidden = False


def _hide_pickup_spoiler(button):
    button.setText("Hidden")
    button.item_is_hidden = True


class SeedDetailsWindow(QMainWindow, Ui_SeedDetailsWindow):
    _on_bulk_change: bool = False
    _history_items: List[QRadioButton] = []
    pickup_spoiler_buttons: List[QPushButton] = []
    layout_description: LayoutDescription

    def __init__(self, json_path: Path):
        super().__init__()
        self.setupUi(self)
        set_default_window_icon(self)
        self.layout_description = LayoutDescription.from_file(json_path)

        # Keep the Layout Description visualizer ready, but invisible.
        self._create_pickup_spoilers()

        # And update
        self.update_layout_description(self.layout_description)

    # Layout Visualization
    def _create_pickup_spoiler_combobox(self):
        self.pickup_spoiler_pickup_combobox.currentTextChanged.connect(self._on_change_pickup_filter)

    def _create_pickup_spoilers(self):
        self.pickup_spoiler_show_all_button.clicked.connect(self._toggle_show_all_pickup_spoiler)
        self.pickup_spoiler_show_all_button.currently_show_all = True

        self._create_pickup_spoiler_combobox()

        game_description = default_prime2_game_description()
        for world in game_description.world_list.worlds:
            group_box = QGroupBox(self.pickup_spoiler_scroll_contents)
            group_box.setTitle(world.name)
            vertical_layout = QVBoxLayout(group_box)
            vertical_layout.setContentsMargins(8, 4, 8, 4)
            vertical_layout.setSpacing(2)
            group_box.vertical_layout = vertical_layout

            vertical_layout.horizontal_layouts = []

            for node in world.all_nodes:
                if not isinstance(node, PickupNode):
                    continue

                horizontal_layout = QHBoxLayout()
                horizontal_layout.setSpacing(2)

                label = QLabel(group_box)
                label.setText(game_description.world_list.node_name(node))
                horizontal_layout.addWidget(label)
                horizontal_layout.label = label

                push_button = QPushButton(group_box)
                push_button.setFlat(True)
                push_button.setText("Hidden")
                push_button.item_is_hidden = True
                push_button.pickup_index = node.pickup_index
                push_button.clicked.connect(partial(self._toggle_pickup_spoiler, push_button))
                push_button.item_name = "Nothing was Set, ohno"
                push_button.row = horizontal_layout
                horizontal_layout.addWidget(push_button)
                horizontal_layout.button = push_button
                self.pickup_spoiler_buttons.append(push_button)

                vertical_layout.addLayout(horizontal_layout)
                vertical_layout.horizontal_layouts.append(horizontal_layout)

            self.pickup_spoiler_scroll_content_layout.addWidget(group_box)

    def create_history_item(self, node):
        button = QRadioButton(self.layout_history_content)
        button.toggled.connect(self.on_select_node)
        button.setText(node)
        self.layout_history_content_layout.addWidget(button)
        self._history_items.append(button)
        return button

    def update_layout_description(self, description: LayoutDescription):
        self.layout_description = description
        self.layout_info_tab.show()

        configuration = description.permalink.layout_configuration
        self.layout_seed_value_label.setText(str(description.permalink.seed_number))
        self.layout_trick_value_label.setText(configuration.trick_level.value)
        self.layout_keys_value_label.setText(str(configuration.sky_temple_keys.value))
        self.layout_elevators_value_label.setText(configuration.elevators.value)

        starting_items = [
            major_item.name if state.num_included_in_starting_items == 1 else "{} {}".format(
                state.num_included_in_starting_items, major_item.name
            )

            for major_item, state in configuration.major_items_configuration.items_state.items()
            if state.num_included_in_starting_items > 0
        ]
        self.layout_starting_items_value_label.setText(
            ", ".join(starting_items)
        )

        # Pickup spoiler combo
        pickup_names = {
            pickup.name
            for pickup in description.patches.pickup_assignment.values()
        }
        self.pickup_spoiler_pickup_combobox.clear()
        self.pickup_spoiler_pickup_combobox.addItem("None")
        for pickup_name in sorted(pickup_names):
            self.pickup_spoiler_pickup_combobox.addItem(pickup_name)

        for pickup_button in self.pickup_spoiler_buttons:
            pickup = description.patches.pickup_assignment.get(pickup_button.pickup_index)
            if pickup is not None:
                pickup_button.item_name = pickup.name
            else:
                pickup_button.item_name = "Nothing"

            if not pickup_button.item_is_hidden:
                pickup_button.setText(pickup_button.item_name)

    def _toggle_pickup_spoiler(self, button):
        if button.item_is_hidden:
            _show_pickup_spoiler(button)
        else:
            _hide_pickup_spoiler(button)
        self._update_show_all_button_state()

    def _toggle_show_all_pickup_spoiler(self):
        if self.pickup_spoiler_show_all_button.currently_show_all:
            action = _show_pickup_spoiler
        else:
            action = _hide_pickup_spoiler

        for button in self.pickup_spoiler_buttons:
            action(button)

        self._update_show_all_button_state()

    def _update_show_all_button_state(self):
        self.pickup_spoiler_show_all_button.currently_show_all = all(
            button.item_is_hidden for button in self.pickup_spoiler_buttons
        )
        if self.pickup_spoiler_show_all_button.currently_show_all:
            self.pickup_spoiler_show_all_button.setText(QtCore.QCoreApplication.translate("HistoryWindow", "Show All"))
        else:
            self.pickup_spoiler_show_all_button.setText(QtCore.QCoreApplication.translate("HistoryWindow", "Hide All"))

    def _on_change_pickup_filter(self, text):
        for button in self.pickup_spoiler_buttons:
            visible = text == "None" or text == button.item_name
            button.setVisible(visible)
            button.row.label.setVisible(visible)
