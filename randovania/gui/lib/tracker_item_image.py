from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QLabel, QWidget

if TYPE_CHECKING:
    from PySide6.QtGui import QMouseEvent, QPixmap


class TrackerItemImage(QLabel):
    is_checked: bool

    def __init__(self, parent: QWidget, transparent_pixmap: QPixmap, opaque_pixmap: QPixmap):
        super().__init__(parent)
        self.transparent_pixmap = transparent_pixmap
        self.opaque_pixmap = opaque_pixmap
        self._ignoring_mouse_events = False
        self.setStyleSheet("QToolTip { color: black; background-color: white; }")

    def set_checked(self, is_opaque: bool):
        self.setPixmap(self.opaque_pixmap if is_opaque else self.transparent_pixmap)
        self.is_checked = is_opaque

    def set_ignore_mouse_events(self, enabled: bool):
        self._ignoring_mouse_events = enabled

    def mouseReleaseEvent(self, event_data: QMouseEvent):
        if self._ignoring_mouse_events:
            return
        if 0 <= event_data.x() <= self.width() and 0 <= event_data.y() <= self.height():
            event_data.accept()
            self.set_checked(not self.is_checked)
