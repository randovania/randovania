from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QEvent, Signal


class ClickableLabel(QtWidgets.QLabel):
    clicked = Signal()
    entered = Signal()
    left = Signal()

    def _is_in_rect(self, event_data: QtGui.QMouseEvent) -> bool:
        return 0 <= event_data.x() <= self.width() and 0 <= event_data.y() <= self.height()

    def mouseReleaseEvent(self, event_data: QtGui.QMouseEvent) -> None:
        if self._is_in_rect(event_data):
            event_data.accept()
            self.clicked.emit()

    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        if self._is_in_rect(event):
            event.accept()
            self.entered.emit()

    def leaveEvent(self, event: QEvent) -> None:
        event.accept()
        self.left.emit()

    def focusInEvent(self, event: QtGui.QFocusEvent) -> None:
        event.accept()
        self.entered.emit()

    def focusOutEvent(self, event: QtGui.QFocusEvent) -> None:
        event.accept()
        self.left.emit()

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        key = event.key()
        if key == QtCore.Qt.Key.Key_Return or key == QtCore.Qt.Key.Key_Space:
            event.accept()
            self.clicked.emit()
