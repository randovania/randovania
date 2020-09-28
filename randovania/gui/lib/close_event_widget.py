from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import Signal


class CloseEventWidget(QtWidgets.QMainWindow):
    CloseEvent = Signal()

    def closeEvent(self, event: QtGui.QCloseEvent):
        self.CloseEvent.emit()
        return super().closeEvent(event)
