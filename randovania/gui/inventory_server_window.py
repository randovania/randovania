from randovania.inventory_server.inventory_server import InventoryServer, InventoryServerStatus
from randovania.gui.generated.inventory_server_ui import Ui_InventoryServerWindow
from randovania.gui.lib import common_qt_lib
from PySide6 import QtWidgets, QtGui, QtCore

class InventoryServerWindow(QtWidgets.QMainWindow, Ui_InventoryServerWindow):

    _app: QtWidgets.QApplication

    def __init__(self, options, game_connection):
        super().__init__()
        self._app = QtWidgets.QApplication.instance()
        self._setup_ui()
        self._setup_event_handlers()

    def _setup_ui(self):
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)
    
    def _setup_event_handlers(self):
        self.inventory_server_button.clicked.connect(self.event_button)
        self.inventory_server_autostart.clicked.connect(self.event_autostart)
        self.inventory_server_port.valueChanged.connect(self.event_port)
        self._app.inventory_server.add_status_change_callback(self.update_ui)

    def update_ui(self, status: InventoryServerStatus):
        self._update_ui_common(status, self._app.inventory_server.get_error())
        if   status is InventoryServerStatus.STOPPED:
            self._update_ui_stopped()
        elif status is InventoryServerStatus.STARTING:
            self._update_ui_starting()
        elif status is InventoryServerStatus.RUNNING:
            self._update_ui_running()
        elif status is InventoryServerStatus.STOPPING:
            self._update_ui_stopping()
        elif status is InventoryServerStatus.ERROR:
            self._update_ui_error()
        else:
            raise ValueError("Invalid inventory server status")
    
    def _update_ui_common(self, status: InventoryServerStatus, error: Exception | None):
        self.inventory_server_autostart.setChecked(self._app.inventory_server.get_autostart())
        self.inventory_server_port.setValue(self._app.inventory_server.get_port())
        self.inventory_server_status.setText("Status: " + status.value + (str(error) if not error is None else ""))
    
    def _update_ui_stopped(self):
        self.inventory_server_button.setEnabled(True)
        self.inventory_server_button.setText("Start server")
        self.inventory_server_port.setEnabled(True)

    def _update_ui_starting(self):
        self.inventory_server_button.setEnabled(False)
        self.inventory_server_button.setText("...")
        self.inventory_server_port.setEnabled(False)

    def _update_ui_running(self):
        self.inventory_server_button.setEnabled(True)
        self.inventory_server_button.setText("Stop server")
        self.inventory_server_port.setEnabled(False)

    def _update_ui_stopping(self):
        self.inventory_server_button.setEnabled(False)
        self.inventory_server_button.setText("...")
        self.inventory_server_port.setEnabled(False)

    def _update_ui_error(self):
        self.inventory_server_button.setEnabled(True)
        self.inventory_server_button.setText("Start server")
        self.inventory_server_port.setEnabled(True)
    
    def event_button(self):
        status = self._app.inventory_server.get_status()
        if   status is InventoryServerStatus.ERROR or status is InventoryServerStatus.STOPPED:
            self._app.inventory_server.start()
        elif status is InventoryServerStatus.RUNNING:
            self._app.inventory_server.stop()

    def event_autostart(self, checked):
        self._app.inventory_server.set_autostart(checked)

    def event_port(self, port_number):
        self._app.inventory_server.set_port(port_number)

