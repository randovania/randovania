from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import Signal


class CloseEventWidget(QtWidgets.QMainWindow):
    CloseEvent = Signal()

    def ignore_close_event(self, event: QtGui.QCloseEvent) -> bool:
        return False

    def closeEvent(self, event: QtGui.QCloseEvent):
        if self.ignore_close_event(event):
            return

        self.CloseEvent.emit()
        return super().closeEvent(event)
