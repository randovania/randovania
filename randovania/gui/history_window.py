import collections
import functools
from functools import partial
from typing import Dict, List, Optional

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QRadioButton, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, \
    QMessageBox, QFileDialog

from randovania.games.prime import binary_data
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.common_qt_lib import application_options, prompt_user_for_input_iso
from randovania.gui.history_window_ui import Ui_HistoryWindow
from randovania.gui.iso_management_window import ISOManagementWindow
from randovania.interface_common import simplified_patcher
from randovania.resolver.data_reader import read_resource_database
from randovania.resolver.layout_description import LayoutDescription
from randovania.resolver.resources import PickupEntry, ResourceDatabase


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


class HistoryWindow(QMainWindow, Ui_HistoryWindow):
    _on_bulk_change: bool = False
    _history_items: List[QRadioButton] = []
    pickup_spoiler_buttons: List[QPushButton] = []
    current_layout_description: Optional[LayoutDescription] = None

    selected_layout_change_signal = pyqtSignal(LayoutDescription)

    def __init__(self, main_window, background_processor: BackgroundTaskMixin):
        super().__init__()
        self.setupUi(self)

        self.main_window = main_window
        self.background_processor = background_processor

        data = binary_data.decode_default_prime2()
        self.resource_database = read_resource_database(data["resource_database"])

        self.layout_history_content_layout.setAlignment(Qt.AlignTop)

        # signals
        self.selected_layout_change_signal.connect(self.update_layout_description)

        # Fill the history page
        self.create_history_items()
        self.layout_history_scroll.hide()  # But hide it for now

        # Keep the Layout Description visualizer ready, but invisible.
        self._create_pickup_spoilers(self.resource_database)

        size_policy = self.layout_info_tab.sizePolicy()
        size_policy.setRetainSizeWhenHidden(True)
        self.layout_info_tab.setSizePolicy(size_policy)
        self.layout_info_tab.hide()

        # Exporting
        self.apply_layout_button.clicked.connect(self.apply_layout)
        self.export_layout_button.clicked.connect(self.export_layout)
        self.import_layout_button.clicked.connect(self.import_layout)

    # Layout History
    def add_new_layout_to_history(self, layout: LayoutDescription):
        self.change_selected_layout(layout)

    def change_selected_layout(self, layout: LayoutDescription):
        self.selected_layout_change_signal.emit(layout)

    # Layout Visualization
    def _create_pickup_spoilers(self, resource_database: ResourceDatabase):
        pickup_by_world: Dict[str, List[PickupEntry]] = collections.defaultdict(list)

        for pickup in resource_database.pickups:
            pickup_by_world[pickup.world].append(pickup)

        self.pickup_spoiler_show_all_button.clicked.connect(self._toggle_show_all_pickup_spoiler)
        self.pickup_spoiler_show_all_button.currently_show_all = True

        self.pickup_spoiler_pickup_combobox.currentTextChanged.connect(self._on_change_pickup_filter)
        for pickup in sorted(resource_database.pickups, key=lambda p: p.item):
            self.pickup_spoiler_pickup_combobox.addItem(pickup.item)

        for world, pickups in pickup_by_world.items():
            group_box = QGroupBox(self.pickup_spoiler_scroll_contents)
            group_box.setTitle(world)
            vertical_layout = QVBoxLayout(group_box)
            vertical_layout.setContentsMargins(8, 4, 8, 4)
            vertical_layout.setSpacing(2)
            group_box.vertical_layout = vertical_layout

            vertical_layout.horizontal_layouts = []
            for pickup in pickups:
                horizontal_layout = QHBoxLayout()
                horizontal_layout.setSpacing(2)

                label = QLabel(group_box)
                label.setText(pickup.room)
                horizontal_layout.addWidget(label)
                horizontal_layout.label = label

                push_button = QPushButton(group_box)
                push_button.setFlat(True)
                push_button.setText("Hidden")
                push_button.item_is_hidden = True
                push_button.clicked.connect(partial(self._toggle_pickup_spoiler, push_button))
                push_button.item_name = pickup.item
                push_button.row = horizontal_layout
                horizontal_layout.addWidget(push_button)
                horizontal_layout.button = push_button
                self.pickup_spoiler_buttons.append(push_button)

                vertical_layout.addLayout(horizontal_layout)
                vertical_layout.horizontal_layouts.append(horizontal_layout)

            self.pickup_spoiler_scroll_content_layout.addWidget(group_box)

    def create_history_items(self):
        is_first = True
        for node in []:
            button = self.create_history_item(node)
            button.setChecked(is_first)
            is_first = False

    def create_history_item(self, node):
        button = QRadioButton(self.layout_history_content)
        button.toggled.connect(self.on_select_node)
        button.setText(node)
        self.layout_history_content_layout.addWidget(button)
        self._history_items.append(button)
        return button

    def update_layout_description(self, layout: LayoutDescription):
        self.current_layout_description = layout
        self.layout_info_tab.show()

        configuration = layout.configuration
        self.layout_seed_value_label.setText(str(layout.seed_number))
        self.layout_logic_value_label.setText(configuration.logic.value)
        self.layout_mode_value_label.setText(configuration.mode.value)
        self.layout_keys_value_label.setText(configuration.sky_temple_keys.value)
        self.layout_item_loss_value_label.setText(configuration.item_loss.value)
        self.layout_elevators_value_label.setText(configuration.elevators.value)
        self.layout_hundo_value_label.setText(configuration.hundo_guaranteed.value)
        self.layout_difficulty_value_label.setText(configuration.difficulty.value)

        for i, pickup_button in enumerate(self.pickup_spoiler_buttons):
            mapping = layout.pickup_mapping[i]
            if mapping is not None:
                pickup = self.resource_database.pickups[mapping]
                pickup_button.item_name = pickup.item
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

    # Exporting
    def apply_layout(self):
        if self.current_layout_description is None:
            raise RuntimeError("Trying to apply_layout, but current_layout_description is None")

        if application_options().advanced_options:
            self.apply_layout_advanced()
        else:
            self.apply_layout_simplified()

    def apply_layout_advanced(self):
        self.background_processor.run_in_background_thread(
            functools.partial(
                simplified_patcher.apply_layout,
                layout=self.current_layout_description
            ),
            "Patching game files...")

    def apply_layout_simplified(self):
        input_iso = prompt_user_for_input_iso(self)
        if input_iso is None:
            return

        self.background_processor.run_in_background_thread(
            functools.partial(
                simplified_patcher.patch_iso_with_existing_layout,
                layout=self.current_layout_description,
                input_iso=input_iso,
            ),
            "Patching ISO...")

    def export_layout(self):
        open_result = QFileDialog.getSaveFileName(
            self,
            caption="Select a file to export the layout to...",
            filter="*.json")
        if not open_result or open_result == ("", ""):
            return

        json_path, extension = open_result

        self.current_layout_description.save_to_file(json_path)

    def import_layout(self):
        open_result = QFileDialog.getOpenFileName(
            self,
            caption="Select a layout file to import...",
            filter="*.json")

        if not open_result or open_result == ("", ""):
            return

        json_path, extension = open_result
        self.add_new_layout_to_history(LayoutDescription.from_file(json_path))
