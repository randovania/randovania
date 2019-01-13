from PySide2.QtCore import Qt, QEvent
from PySide2.QtWidgets import QSpinBox


class CustomSpinBox(QSpinBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)

    def focusInEvent(self, event: QEvent):
        self.setFocusPolicy(Qt.WheelFocus)

    def focusOutEvent(self, event: QEvent):
        self.setFocusPolicy(Qt.StrongFocus)

    def eventFilter(self, obj: QSpinBox, event: QEvent) -> bool:
        if event.type() == QEvent.Wheel and isinstance(obj, QSpinBox):
            if obj.focusPolicy() == Qt.WheelFocus:
                event.accept()
                return False
            else:
                event.ignore()
                return True
        return super().eventFilter(obj, event)
