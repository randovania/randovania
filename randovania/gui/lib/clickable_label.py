from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Signal, QEvent


class ClickableLabel(QtWidgets.QLabel):
    clicked = Signal()
    entered = Signal()
    left = Signal()

    def _is_in_rect(self, event_data: QtGui.QMouseEvent) -> bool:
        return 0 <= event_data.x() <= self.width() and 0 <= event_data.y() <= self.height()

    def mouseReleaseEvent(self, event_data: QtGui.QMouseEvent):
        if self._is_in_rect(event_data):
            event_data.accept()
            self.clicked.emit()

    def enterEvent(self, event: QtGui.QEnterEvent):
        if self._is_in_rect(event):
            event.accept()
            self.entered.emit()
    
    def leaveEvent(self, event: QEvent):
        event.accept()
        self.left.emit()
