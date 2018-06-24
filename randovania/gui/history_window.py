import collections
from typing import Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QRadioButton, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from randovania.games.prime import binary_data
from randovania.gui.collapsible_dialog import CollapsibleDialog
from randovania.gui.history_window_ui import Ui_HistoryWindow
from randovania.resolver.data_reader import read_resource_database
from randovania.resolver.resources import PickupEntry


def _unique(iterable):
    seen = set()

    for item in iterable:
        if item in seen:
            continue
        seen.add(item)
        yield item


class HistoryWindow(QMainWindow, Ui_HistoryWindow):
    _on_bulk_change: bool = False

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        data = binary_data.decode_default_prime2()
        resource_database = read_resource_database(data["resource_database"])

        self.is_100_completable_guaranteed.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.is_oob_allowed.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.is_item_loss_removed.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.are_elevators_randomized.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.layout_history_content_layout.setAlignment(Qt.AlignTop)
        is_first = True
        for node in ["foo", "bar"]:
            button = QRadioButton(self.layout_history_content)
            # button.toggled.connect(self.on_select_node)
            button.setText(node)
            button.setChecked(is_first)
            is_first = False
            self.layout_history_content_layout.addWidget(button)

        pickup_by_world: Dict[str, List[PickupEntry]] = collections.defaultdict(list)
        for pickup in resource_database.pickups:
            pickup_by_world[pickup.world].append(pickup)

        # self.pickupSpoilerContentLayout.setAlignment(Qt.AlignTop)
        self.pickup_spoiler_boxes = []

        for world, pickups in pickup_by_world.items():
            group_box = QGroupBox(self.pickup_spoiler_scroll_contents)
            group_box.setTitle(world)
            # group_box.setCheckable(True)
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
                push_button.setText(pickup.item)
                horizontal_layout.addWidget(push_button)
                horizontal_layout.button = push_button

                vertical_layout.addLayout(horizontal_layout)
                vertical_layout.horizontal_layouts.append(horizontal_layout)

            self.pickup_spoiler_scroll_content_layout.addWidget(group_box)
            self.pickup_spoiler_boxes.append(group_box)

        self.solver_path_contents.hide()
