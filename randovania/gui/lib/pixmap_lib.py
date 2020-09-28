from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QPixmap, QImage, QPainter


def paint_with_opacity(pixmap: QPixmap, opacity: float):
    transparent_image = QImage(QSize(36, 36), QImage.Format_ARGB32_Premultiplied)
    transparent_image.fill(Qt.transparent)
    painter = QPainter(transparent_image)
    painter.setOpacity(opacity)
    painter.drawPixmap(18 - pixmap.width() / 2,
                       18 - pixmap.height() / 2,
                       pixmap)
    painter.end()
    return QPixmap.fromImage(transparent_image)
