from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPixmap


def paint_with_opacity(pixmap: QPixmap, opacity: float):
    transparent_image = QImage(pixmap.size(), QImage.Format.Format_ARGB32_Premultiplied)
    transparent_image.fill(Qt.transparent)
    painter = QPainter(transparent_image)
    painter.setOpacity(opacity)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return QPixmap.fromImage(transparent_image)
