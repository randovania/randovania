from __future__ import annotations

from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import Signal


class CloseEventWindow(QtWidgets.QMainWindow):
    CloseEvent = Signal()

    def ignore_close_event(self, event: QtGui.QCloseEvent) -> bool:
        return False

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self.ignore_close_event(event):
            return

        self.CloseEvent.emit()
        super().closeEvent(event)
