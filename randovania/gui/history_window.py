import collections
import random
from functools import partial
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QRadioButton, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from randovania import VERSION
from randovania.games.prime import binary_data
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.history_window_ui import Ui_HistoryWindow
from randovania.resolver.echoes import generate_layout
from randovania.resolver.layout_description import LayoutDescription, SolverPath
from randovania.resolver.layout_configuration import LayoutLogic, LayoutMode, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutDifficulty, LayoutConfiguration
from randovania.resolver.data_reader import read_resource_database
from randovania.resolver.resources import PickupEntry


def _unique(iterable):
    seen = set()

    for item in iterable:
        if item in seen:
            continue
        seen.add(item)
        yield item


class HistoryWindow(QMainWindow, Ui_HistoryWindow, BackgroundTaskMixin):
    _on_bulk_change: bool = False
    _history_items: List[QRadioButton] = []
    pickup_spoiler_buttons: List[QPushButton] = []
    current_layout_description: Optional[LayoutDescription] = None

    layout_generated_signal = pyqtSignal(LayoutDescription)
    selected_layout_change_signal = pyqtSignal(LayoutDescription)

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        data = binary_data.decode_default_prime2()
        self.resource_database = read_resource_database(data["resource_database"])

        self.layout_history_content_layout.setAlignment(Qt.AlignTop)

        # signals
        self.layout_generated_signal.connect(self._on_layout_generated)
        self.selected_layout_change_signal.connect(self.update_layout_description)

        # All code for the Randomize button
        self.seed_number_edit.setValidator(QIntValidator(0, 2 ** 31 - 1))
        self.setup_layout_combo_data()
        self.setup_initial_combo_selection()
        self.create_layout_button.clicked.connect(self.create_new_layout)

        # Fill the history page
        self.create_history_items()
        self.history_box.hide()  # But hide it for now

        # Keep the Layout Description visualizer ready, but invisible.
        self._create_pickup_spoilers(self.resource_database)
        self.layout_info_tab.hide()

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
        self.logic_selection_combo.setItemData(1, LayoutLogic.NORMAL)
        self.logic_selection_combo.setItemData(2, LayoutLogic.HARD)
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
        self.randomize_in_progress_bar.setValue(1)
        self.randomize_in_progress_bar.setMaximum(1)
        self.selected_layout_change_signal.emit(layout)

    def create_new_layout(self):
        self.randomize_in_progress_bar.setValue(0)
        self.randomize_in_progress_bar.setMaximum(0)

        def work(status_update):
            self.layout_generated_signal.emit(
                generate_layout(
                    data=binary_data.decode_default_prime2(),
                    configuration=self.currently_selected_layout_configuration,
                )
            )

        self.run_in_background_thread(work, "Randomizing...")

    def _create_pickup_spoilers(self, resource_database):
        pickup_by_world: Dict[str, List[PickupEntry]] = collections.defaultdict(list)

        for pickup in resource_database.pickups:
            pickup_by_world[pickup.world].append(pickup)

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

    def _toggle_pickup_spoiler(self, button):
        if button.item_is_hidden:
            button.setText(button.item_name)
            button.item_is_hidden = False
        else:
            button.setText("Hidden")
            button.item_is_hidden = True

    def _on_change_pickup_filter(self, text):
        for button in self.pickup_spoiler_buttons:
            visible = text == "None" or text == button.item_name
            button.setVisible(visible)
            button.row.label.setVisible(visible)

