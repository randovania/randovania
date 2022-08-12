from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Signal


class ClickableLabel(QtWidgets.QLabel):
    clicked = Signal()

    def mouseReleaseEvent(self, event_data: QtGui.QMouseEvent):
        if 0 <= event_data.x() <= self.width() and 0 <= event_data.y() <= self.height():
            event_data.accept()
            self.clicked.emit()
