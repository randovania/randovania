import collections
import random
from functools import partial
from typing import Dict, List, Optional, Callable

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QRadioButton, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, \
    QMessageBox, QFileDialog

from randovania.games.prime import binary_data
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.history_window_ui import Ui_HistoryWindow
from randovania.gui.iso_management_window import ISOManagementWindow
from randovania.resolver.data_reader import read_resource_database
from randovania.resolver.echoes import generate_layout
from randovania.resolver.layout_configuration import LayoutLogic, LayoutMode, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutDifficulty, LayoutConfiguration
from randovania.resolver.layout_description import LayoutDescription
from randovania.resolver.resources import PickupEntry


def _unique(iterable):
    seen = set()

    for item in iterable:
        if item in seen:
            continue
        seen.add(item)
        yield item


def show_failed_generation_exception(exception: Exception):
    QMessageBox.critical(None,
                         "An exception was raised",
                         "An unhandled Exception occurred:\n{}".format(exception))


def _show_pickup_spoiler(button):
    button.setText(button.item_name)
    button.item_is_hidden = False


def _hide_pickup_spoiler(button):
    button.setText("Hidden")
    button.item_is_hidden = True


class HistoryWindow(QMainWindow, Ui_HistoryWindow, BackgroundTaskMixin):
    _on_bulk_change: bool = False
    _history_items: List[QRadioButton] = []
    pickup_spoiler_buttons: List[QPushButton] = []
    current_layout_description: Optional[LayoutDescription] = None

    layout_generated_signal = pyqtSignal(LayoutDescription)
    selected_layout_change_signal = pyqtSignal(LayoutDescription)
    failed_to_generate_signal = pyqtSignal(Exception)

    def __init__(self, main_window):
        super().__init__()
        self.setupUi(self)

        self.main_window = main_window

        data = binary_data.decode_default_prime2()
        self.resource_database = read_resource_database(data["resource_database"])

        self.layout_history_content_layout.setAlignment(Qt.AlignTop)

        # signals
        self.progress_update_signal.connect(self.update_progress)
        self.layout_generated_signal.connect(self._on_layout_generated)
        self.selected_layout_change_signal.connect(self.update_layout_description)
        self.failed_to_generate_signal.connect(show_failed_generation_exception)
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)

        # All code for the Randomize button
        self.seed_number_edit.setValidator(QIntValidator(0, 2 ** 31 - 1))
        self.setup_layout_combo_data()
        self.setup_initial_combo_selection()
        self.create_layout_button.clicked.connect(self.create_new_layout)
        self.abort_create_button.clicked.connect(self.stop_background_process)

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

    # Layout Creation logic
    @property
    def currently_selected_layout_configuration(self) -> LayoutConfiguration:
        seed = self.seed_number_edit.text()
        if seed == "":
            seed = random.randint(0, 2 ** 31)
        else:
            seed = int(seed)
        return LayoutConfiguration(
            seed_number=seed,
            logic=self.logic_selection_combo.currentData(),
            mode=self.mode_selection_combo.currentData(),
            sky_temple_keys=self.keys_selection_combo.currentData(),
            item_loss=self.item_loss_selection_combo.currentData(),
            elevators=self.elevators_selection_combo.currentData(),
            hundo_guaranteed=self.guaranteed_100_selection_combo.currentData(),
            difficulty=self.difficulty_selection_combo.currentData(),
        )

    def setup_layout_combo_data(self):
        self.keys_selection_combo.setItemData(0, LayoutRandomizedFlag.VANILLA)
        self.keys_selection_combo.setItemData(1, LayoutRandomizedFlag.RANDOMIZED)
        self.logic_selection_combo.setItemData(0, LayoutLogic.NO_GLITCHES)
        self.logic_selection_combo.setItemData(1, LayoutLogic.EASY)
        self.logic_selection_combo.setItemData(2, LayoutLogic.NORMAL)
        self.logic_selection_combo.setItemData(3, LayoutLogic.HARD)
        self.mode_selection_combo.setItemData(0, LayoutMode.STANDARD)
        self.mode_selection_combo.setItemData(1, LayoutMode.MAJOR_ITEMS)
        self.difficulty_selection_combo.setItemData(0, LayoutDifficulty.NORMAL)
        self.item_loss_selection_combo.setItemData(0, LayoutEnabledFlag.ENABLED)
        self.item_loss_selection_combo.setItemData(1, LayoutEnabledFlag.DISABLED)
        self.elevators_selection_combo.setItemData(0, LayoutRandomizedFlag.VANILLA)
        self.elevators_selection_combo.setItemData(1, LayoutRandomizedFlag.RANDOMIZED)
        self.guaranteed_100_selection_combo.setItemData(0, LayoutEnabledFlag.ENABLED)
        self.guaranteed_100_selection_combo.setItemData(1, LayoutEnabledFlag.DISABLED)

    def setup_initial_combo_selection(self):
        self.keys_selection_combo.setCurrentIndex(1)
        self.guaranteed_100_selection_combo.setCurrentIndex(1)

    def _on_layout_generated(self, layout: LayoutDescription):
        self.selected_layout_change_signal.emit(layout)

    def create_new_layout(self):

        def work(status_update: Callable[[str, int], None]):
            def status_wrapper(message: str):
                status_update(message, -1)

            resulting_layout = generate_layout(
                data=binary_data.decode_default_prime2(),
                configuration=self.currently_selected_layout_configuration,
                status_update=status_wrapper
            )
            if isinstance(resulting_layout, Exception):
                self.failed_to_generate_signal.emit(resulting_layout)
                status_update("Error: {}".format(resulting_layout), 100)
            else:
                self.layout_generated_signal.emit(resulting_layout)
                status_update("Success!", 100)

        self.run_in_background_thread(work, "Randomizing...")

    def _create_pickup_spoilers(self, resource_database):
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
        self.main_window.get_tab(ISOManagementWindow).load_layout(self.current_layout_description)

        configuration = layout.configuration
        self.layout_seed_value_label.setText(str(configuration.seed_number))
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
        self.main_window.focus_tab(self.main_window.get_tab(ISOManagementWindow))

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
        self.layout_generated_signal.emit(LayoutDescription.from_file(json_path))

    def update_progress(self, message: str, percentage: int):
        self.randomize_in_progress_status.setText(message)
        if "Aborted" in message:
            percentage = 0
        if percentage >= 0:
            self.randomize_in_progress_bar.setRange(0, 100)
            self.randomize_in_progress_bar.setValue(percentage)
        else:
            self.randomize_in_progress_bar.setRange(0, 0)

    def enable_buttons_with_background_tasks(self, value: bool):
        self.create_layout_button.setEnabled(value)
        self.abort_create_button.setEnabled(not value)
