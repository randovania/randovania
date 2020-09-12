import collections
import itertools
from typing import List, TypeVar, Type, Iterator

from PySide2 import QtWidgets
from PySide2.QtWidgets import QMainWindow
from asyncqt import asyncSlot

from randovania.game_connection.connection_backend import ConnectionBackend, ConnectionStatus
from randovania.game_description import default_database
from randovania.game_description.node import PickupNode
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.gui.generated.debug_backend_window_ui import Ui_DebugBackendWindow
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.qt_network_client import handle_network_errors
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.network_common.admin_actions import SessionAdminUserAction

T = TypeVar("T")


def iterate_enum(enum_class: Type[T]) -> Iterator[T]:
    yield from enum_class


class DebugBackendWindow(ConnectionBackend, Ui_DebugBackendWindow):
    pickups: List[PickupEntry]
    permanent_pickups: List[PickupEntry]
    _inventory: CurrentResources

    def __init__(self):
        super().__init__()
        self.window = QMainWindow()
        self.setupUi(self.window)
        common_qt_lib.set_default_window_icon(self.window)

        for status in iterate_enum(ConnectionStatus):
            self.current_status_combo.addItem(status.pretty_text, status)

        self.permanent_pickups = []
        self.pickups = []
        self._inventory = {}

        self.collect_location_combo.setVisible(False)
        self.setup_collect_location_combo_button = QtWidgets.QPushButton(self.window)
        self.setup_collect_location_combo_button.setText("Load list of locations")
        self.setup_collect_location_combo_button.clicked.connect(self._setup_locations_combo)
        self.gridLayout.addWidget(self.setup_collect_location_combo_button, 1, 0, 1, 1)

        self.collect_location_button.clicked.connect(self._emit_collection)
        self.collect_location_button.setEnabled(False)

    @property
    def current_status(self) -> ConnectionStatus:
        return self.current_status_combo.currentData()

    def display_message(self, message: str):
        self.messages_list.addItem(message)

    async def get_inventory(self) -> CurrentResources:
        return self._inventory

    def send_pickup(self, pickup: PickupEntry):
        self.pickups.append(pickup)
        self._update_inventory()

    def set_permanent_pickups(self, pickups: List[PickupEntry]):
        self.permanent_pickups = pickups
        self._update_inventory()

    def _update_inventory(self):
        inventory = collections.defaultdict(int)
        for pickup in itertools.chain(self.pickups, self.permanent_pickups):
            inventory[pickup.name] += 1

        self.inventory_label.setText("<br />".join(
            f"{name} x{quantity}" for name, quantity in sorted(inventory.items())
        ))

    @property
    def name(self) -> str:
        return "Debug"

    async def update(self, dt: float):
        pass

    def show(self):
        self.window.show()

    def _emit_collection(self):
        self.LocationCollected.emit(self.collect_location_combo.currentData())

    @asyncSlot()
    @handle_network_errors
    async def _setup_locations_combo(self):
        network_client = common_qt_lib.get_network_client()
        game_session = network_client.current_game_session
        user = network_client.current_user

        patcher_data = await network_client.session_admin_player(game_session.id, user.id,
                                                                 SessionAdminUserAction.CREATE_PATCHER_FILE,
                                                                 CosmeticPatches().as_json)

        game = default_database.default_prime2_game_description()
        index_to_name = {
            node.pickup_index.index: game.world_list.area_name(area, distinguish_dark_aether=True, separator=" - ")
            for world, area, node in game.world_list.all_worlds_areas_nodes
            if isinstance(node, PickupNode)
        }

        names = {}
        for pickup in patcher_data["pickups"]:
            names[pickup["pickup_index"]] = "{}: {}".format(index_to_name[pickup["pickup_index"]],
                                                            pickup["hud_text"][0])

        self.collect_location_combo.clear()
        for index, name in sorted(names.items()):
            self.collect_location_combo.addItem(name, index)

        self.collect_location_button.setEnabled(True)
        self.collect_location_combo.setVisible(True)
        self.setup_collect_location_combo_button.deleteLater()

    def clear(self):
        self.messages_list.clear()
        self.permanent_pickups = []
        self.pickups.clear()
        self._update_inventory()
