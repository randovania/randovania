from __future__ import annotations

from PySide6 import QtWidgets
from PySide6.QtCore import QEvent, Qt


class ScrollProtectedSlider(QtWidgets.QSlider):
    def __init__(self, orientation: Qt.Orientation, parent: QtWidgets.QWidget | None = None):
        super().__init__(orientation, parent)
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)

    def focusInEvent(self, event: QEvent):
        self.setFocusPolicy(Qt.WheelFocus)

    def focusOutEvent(self, event: QEvent):
        self.setFocusPolicy(Qt.StrongFocus)

    def eventFilter(self, obj: QtWidgets.QSluider, event: QEvent) -> bool:
        if event.type() == QEvent.Wheel and isinstance(obj, QtWidgets.QSlider):
            if obj.focusPolicy() == Qt.WheelFocus:
                event.accept()
                return False
            else:
                event.ignore()
                return True
        return super().eventFilter(obj, event)


class ScrollProtectedSpinBox(QtWidgets.QSpinBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)

    def focusInEvent(self, event: QEvent):
        self.setFocusPolicy(Qt.WheelFocus)

    def focusOutEvent(self, event: QEvent):
        self.setFocusPolicy(Qt.StrongFocus)

    def eventFilter(self, obj: QtWidgets.QSpinBox, event: QEvent) -> bool:
        if event.type() == QEvent.Wheel and isinstance(obj, QtWidgets.QSpinBox):
            if obj.focusPolicy() == Qt.WheelFocus:
                event.accept()
                return False
            else:
                event.ignore()
                return True
        return super().eventFilter(obj, event)


class ScrollProtectedComboBox(QtWidgets.QComboBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)

    def focusInEvent(self, event: QEvent):
        self.setFocusPolicy(Qt.WheelFocus)

    def focusOutEvent(self, event: QEvent):
        self.setFocusPolicy(Qt.StrongFocus)

    def eventFilter(self, obj: QtWidgets.QComboBox, event: QEvent) -> bool:
        if event.type() == QEvent.Wheel and isinstance(obj, QtWidgets.QComboBox):
            if obj.focusPolicy() == Qt.WheelFocus:
                event.accept()
                return False
            else:
                event.ignore()
                return True
        return super().eventFilter(obj, event)
