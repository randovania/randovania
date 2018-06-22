from PyQt5.QtWidgets import QMainWindow

from randovania.gui.collapsible_dialog import CollapsibleDialog
from randovania.gui.history_window_ui import Ui_HistoryWindow


class HistoryWindow(QMainWindow, Ui_HistoryWindow):
    _on_bulk_change: bool = False

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # window = CollapsibleDialog()
        # window.show()
