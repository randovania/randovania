from pathlib import Path
from typing import Optional, Dict

import PySide2
import slugify
from PySide2.QtCore import QTimer, Signal, Qt
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QMainWindow, QLabel
from asyncqt import asyncSlot

from randovania import get_data_path
from randovania.game_connection.connection_base import GameConnectionStatus, InventoryItem
from randovania.game_connection.game_connection import GameConnection
from randovania.game_description import data_reader
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_database import find_resource_info_with_long_name
from randovania.games.prime import default_data
from randovania.gui.generated.auto_tracker_window_ui import Ui_AutoTrackerWindow
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.clickable_label import ClickableLabel
from randovania.gui.lib.game_connection_setup import GameConnectionSetup
from randovania.gui.lib.pixmap_lib import paint_with_opacity
from randovania.interface_common.options import Options


class AutoTrackerWindow(QMainWindow, Ui_AutoTrackerWindow):
    _hooked = False
    _base_address: int
    give_item_signal = Signal(PickupEntry)

    def __init__(self, game_connection: GameConnection, options: Options):
        super().__init__()
        self.setupUi(self)
        self.game_connection = game_connection
        common_qt_lib.set_default_window_icon(self)

        self.game_data = data_reader.decode_data(default_data.decode_default_prime2())
        self._energy_tank_item = find_resource_info_with_long_name(self.game_data.resource_database.item, "Energy Tank")

        self._item_to_label: Dict[ItemResourceInfo, ClickableLabel] = {}
        self._labels_for_keys = []
        self.create_tracker()

        self.game_connection_setup = GameConnectionSetup(self, self.game_connection_tool, self.connection_status_label,
                                                         self.game_connection, options)
        self.force_update_button.setEnabled(not options.tracking_inventory)
        self.force_update_button.clicked.connect(self.on_force_update_button)

        self._update_timer = QTimer(self)
        self._update_timer.setInterval(100)
        self._update_timer.timeout.connect(self._on_timer_update)
        self._update_timer.setSingleShot(True)

    def showEvent(self, event: PySide2.QtGui.QShowEvent):
        self._update_timer.start()
        super().showEvent(event)

    def hideEvent(self, event: PySide2.QtGui.QHideEvent):
        self._update_timer.stop()
        super().hideEvent(event)

    def _update_tracker_from_hook(self, inventory: Dict[ItemResourceInfo, InventoryItem]):
        for item, label in self._item_to_label.items():
            current = inventory.get(item, InventoryItem(0, 0))
            label.set_checked(current.capacity > 0)

        energy_tank = inventory.get(self._energy_tank_item, InventoryItem(0, 0))
        self._energy_tank_label.setText("x {}/{}".format(energy_tank.capacity, self._energy_tank_item.max_capacity))

        for label, keys in self._labels_for_keys:
            num_keys = sum(inventory.get(key, InventoryItem(0, 0)).capacity for key in keys)
            label.setText("x {}/{}".format(num_keys, len(keys)))

    @asyncSlot()
    async def _on_timer_update(self):
        try:
            self.force_update_button.setEnabled(not self.game_connection.tracking_inventory)
            current_status = self.game_connection.current_status
            if current_status == GameConnectionStatus.InGame or current_status == GameConnectionStatus.TrackerOnly:
                inventory = self.game_connection.get_current_inventory()
                self._update_tracker_from_hook(inventory)
        finally:
            self._update_timer.start()

    def create_tracker(self):
        def get_image_path(image_name: str) -> Path:
            return get_data_path().joinpath(f"gui_assets/tracker/images-noanim/{image_name}.gif")

        def find_resource(name: str):
            return find_resource_info_with_long_name(self.game_data.resource_database.item, name)

        def create_item(image_name: str, always_opaque: bool = False):
            image_path = get_image_path(image_name)
            pixmap = QPixmap(str(image_path))

            label = ClickableLabel(self.inventory_group, paint_with_opacity(pixmap, 0.3),
                                   paint_with_opacity(pixmap, 1.0))
            label.set_checked(always_opaque)
            label.set_ignore_mouse_events(always_opaque)

            return label

        def add_item(row: int, column: int, item_name: str, image_name: Optional[str] = None):
            if image_name is None:
                image_name = slugify.slugify(item_name).replace("-", "_")

            label = create_item(image_name)
            label.set_ignore_mouse_events(True)
            self.inventory_layout.addWidget(label, row, column)

            self._item_to_label[find_resource(item_name)] = label

        add_item(0, 0, "Charge Beam")
        add_item(1, 0, "Missile Launcher")
        add_item(2, 0, "Super Missile")
        add_item(3, 0, "Seeker Launcher")

        add_item(0, 1, "Dark Beam")
        add_item(0, 2, "Light Beam")
        add_item(0, 3, "Annihilator Beam")
        add_item(1, 1, "Darkburst")
        add_item(1, 2, "Sunburst")
        add_item(1, 3, "Sonic Boom")

        add_item(2, 2, "Scan Visor")
        add_item(2, 3, "Dark Visor")
        add_item(2, 4, "Echo Visor")

        add_item(3, 1, "Space Jump Boots")
        add_item(3, 2, "Gravity Boost")
        add_item(3, 3, "Grapple Beam")
        add_item(3, 4, "Screw Attack")

        add_item(0, 4, "Dark Suit")
        add_item(1, 4, "Light Suit")

        add_item(0, 5, "Morph Ball Bomb")
        add_item(1, 5, "Power Bomb")
        add_item(2, 5, "Boost Ball")
        add_item(3, 5, "Spider Ball")

        add_item(0, 6, "Violet Translator")
        add_item(1, 6, "Amber Translator")
        add_item(2, 6, "Emerald Translator")
        add_item(3, 6, "Cobalt Translator")

        add_item(2, 1, "Energy Transfer Module")

        self.inventory_layout.addWidget(create_item("energy_tank", True), 5, 1)
        energy_tank_label = QLabel(self.inventory_group)
        energy_tank_label.setText("x 0/14")
        energy_tank_label.setAlignment(Qt.AlignCenter)
        self.inventory_layout.addWidget(energy_tank_label, 6, 1)
        self._energy_tank_label = energy_tank_label

        self.inventory_layout.addWidget(create_item("dark_agon_key-recolored", True), 5, 2)
        dark_agon_key_label = QLabel(self.inventory_group)
        dark_agon_key_label.setText("x 0/3")
        dark_agon_key_label.setAlignment(Qt.AlignCenter)
        self.inventory_layout.addWidget(dark_agon_key_label, 6, 2)
        self._labels_for_keys.append((
            dark_agon_key_label,
            (find_resource("Dark Agon Key 1"), find_resource("Dark Agon Key 2"), find_resource("Dark Agon Key 3"))
        ))

        self.inventory_layout.addWidget(create_item("dark_torvus_key-recolored", True), 5, 3)
        dark_torvus_key_label = QLabel(self.inventory_group)
        dark_torvus_key_label.setText("x 0/3")
        dark_torvus_key_label.setAlignment(Qt.AlignCenter)
        self.inventory_layout.addWidget(dark_torvus_key_label, 6, 3)
        self._labels_for_keys.append((
            dark_torvus_key_label,
            (find_resource("Dark Torvus Key 1"), find_resource("Dark Torvus Key 2"), find_resource("Dark Torvus Key 3"))
        ))

        self.inventory_layout.addWidget(create_item("ing_hive_key-recolored", True), 5, 4)
        ing_hive_key_label = QLabel(self.inventory_group)
        ing_hive_key_label.setText("x 0/3")
        ing_hive_key_label.setAlignment(Qt.AlignCenter)
        self.inventory_layout.addWidget(ing_hive_key_label, 6, 4)
        self._labels_for_keys.append((
            ing_hive_key_label,
            (find_resource("Ing Hive Key 1"), find_resource("Ing Hive Key 2"), find_resource("Ing Hive Key 3"))
        ))

        self.inventory_layout.addWidget(create_item("sky_temple_key", True), 5, 5)
        sky_temple_key_label = QLabel(self.inventory_group)
        sky_temple_key_label.setText("x 0/9")
        sky_temple_key_label.setAlignment(Qt.AlignCenter)
        self.inventory_layout.addWidget(sky_temple_key_label, 6, 5)
        self._labels_for_keys.append((
            sky_temple_key_label,
            (find_resource("Sky Temple Key 1"), find_resource("Sky Temple Key 2"), find_resource("Sky Temple Key 3"),
             find_resource("Sky Temple Key 4"), find_resource("Sky Temple Key 5"), find_resource("Sky Temple Key 6"),
             find_resource("Sky Temple Key 7"), find_resource("Sky Temple Key 8"), find_resource("Sky Temple Key 9"),)
        ))

    @asyncSlot()
    async def on_force_update_button(self):
        await self.game_connection.backend.update_current_inventory()
