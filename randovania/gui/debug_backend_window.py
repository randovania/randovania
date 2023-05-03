import random

from PySide6 import QtCore
from PySide6.QtWidgets import QMainWindow
from qasync import asyncSlot

from randovania.game_connection.connector.debug_remote_connector import DebugRemoteConnector
from randovania.game_description import default_database
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.pickup_node import PickupNode
from randovania.gui.generated.debug_connector_window_ui import Ui_DebugConnectorWindow
from randovania.gui.lib import common_qt_lib


class DebugConnectorWindow(Ui_DebugConnectorWindow):
    _connected: bool = False
    _timer: QtCore.QTimer

    def __init__(self, connector: DebugRemoteConnector):
        super().__init__()
        self.window = QMainWindow()
        self.setupUi(self.window)
        common_qt_lib.set_default_window_icon(self.window)

        self.connector = connector
        connector.RemotePickupsUpdated.connect(self._on_remote_pickups)

        self.reset_button.clicked.connect(self.finish)

        self.collect_location_combo.setVisible(False)
        self.collect_location_button.clicked.connect(self._emit_collection)
        self.collect_location_button.setEnabled(False)
        self.collect_randomly_check.stateChanged.connect(self._on_collect_randomly_toggle)

        self._timer = QtCore.QTimer(self.window)
        self._timer.timeout.connect(self._collect_randomly)
        self._timer.setInterval(10000)

        self._setup_locations_combo()
        self._on_remote_pickups()

    def _on_collect_randomly_toggle(self, value: int):
        if bool(value):
            self._timer.start()
        else:
            self._timer.stop()

    def _collect_randomly(self):
        row = random.randint(0, self.collect_location_combo.count())
        self._collect_location(self.collect_location_combo.itemData(row))

    def show(self):
        self.window.show()

    def _emit_collection(self):
        self._collect_location(self.collect_location_combo.currentData())

    def _collect_location(self, location: int):
        self.connector.PickupIndexCollected.emit(PickupIndex(location))

    def _setup_locations_combo(self):
        game = default_database.game_description_for(self.connector.game_enum)
        index_to_name = {
            node.pickup_index.index: game.world_list.area_name(area)
            for world, area, node in game.world_list.all_worlds_areas_nodes
            if isinstance(node, PickupNode)
        }

        names = index_to_name

        self.collect_location_combo.clear()
        for index, name in sorted(names.items(), key=lambda t: t[1]):
            self.collect_location_combo.addItem(name, index)

        self.collect_location_button.setEnabled(True)
        self.collect_location_combo.setVisible(True)

    @asyncSlot()
    async def finish(self):
        await self.connector.force_finish()
        self.window.close()

    def _on_remote_pickups(self):
        self.messages_list.clear()
        for player, pickup in self.connector.remote_pickups:
            self.messages_list.addItem(f"Received {pickup.name} from {player}")
