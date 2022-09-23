from randovania.inventory_server.inventory_server import InventoryServer
from randovania.gui.generated.inventory_server_ui import Ui_InventoryServerWindow
from randovania.gui.lib import common_qt_lib
from PySide6 import QtWidgets, QtGui, QtCore

class InventoryServerWindow(QtWidgets.QMainWindow, Ui_InventoryServerWindow):

    _app: QtWidgets.QApplication

    def __init__(self, options, game_connection):
        super().__init__()
        self._setup_ui()
        self._setup_event_handlers()
        self._app = QtWidgets.QApplication.instance()
        self._update_ui()

    def _setup_event_handlers(self):
        self.inventory_server_start_button.clicked.connect(self.event_start_button)
        self.inventory_server_stop_button.clicked.connect(self.event_stop_button)
        self.inventory_server_autostart.clicked.connect(self.event_autostart)
        self.inventory_server_port.valueChanged.connect(self.event_port)

    def _setup_ui(self):
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)
    
    def _update_ui(self):
        self.inventory_server_autostart.setChecked(self._app.inventory_server.get_autostart())
        self.inventory_server_port.setValue(self._app.inventory_server.get_port())
        self.inventory_server_port.setEnabled(not self._app.inventory_server.is_running)
        self.inventory_server_start_button.setEnabled(not self._app.inventory_server.is_running)
        self.inventory_server_start_button.setText("Running..." if self._app.inventory_server.is_running else "Start server")
        self.inventory_server_stop_button.setEnabled(self._app.inventory_server.is_running)
        self.inventory_server_stop_button.setText("Stop server" if self._app.inventory_server.is_running else "Stopped")

    def event_start_button(self):
        if not self._app.inventory_server.is_running:
            self._app.inventory_server.start()
        self._update_ui()

    def event_stop_button(self):
        if self._app.inventory_server.is_running:
            self._app.inventory_server.stop()
        self._update_ui()

    def event_autostart(self, checked):
        self._app.inventory_server.set_autostart(checked)

    def event_port(self, port_number):
        self._app.inventory_server.set_port(port_number)

