import math
from typing import Optional, Type

from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import QPointF, QRectF

from randovania.game_description.world.area import Area
from randovania.game_description.world.node import GenericNode, DockNode, TeleporterNode, PickupNode, EventNode, Node

_color_for_node: dict[Type[Node], int] = {
    GenericNode: QtGui.Qt.red,
    DockNode: QtGui.Qt.green,
    TeleporterNode: QtGui.Qt.blue,
    PickupNode: QtGui.Qt.cyan,
    EventNode: QtGui.Qt.magenta,
}


class DataEditorCanvas(QtWidgets.QWidget):
    area: Optional[Area] = None
    highlighted_node: Optional[Node] = None

    def select_area(self, area: Area):
        self.area = area
        self.update()

    def highlight_node(self, node: Node):
        self.highlighted_node = node
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        area = self.area

        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.Qt.white)
        painter.setFont(QtGui.QFont("Arial", 10))

        border = 75
        canvas_width = self.rect().width() - border * 2
        canvas_height = self.rect().height() - border * 2
        painter.translate(border, border)

        def centeredText(pos: QPointF, text: str):
            rect = QRectF(pos.x() - 32767 * 0.5, pos.y() - 32767 * 0.5, 32767, 32767)
            painter.drawText(rect, QtGui.Qt.AlignCenter, text)

        if area is not None:
            if "total_boundings" in area.extra:
                min_x, max_x, min_y, max_y = [area.extra["total_boundings"][k] for k in ["x1", "x2", "y1", "y2"]]
            else:
                min_x, min_y = math.inf, math.inf
                max_x, max_y = -math.inf, -math.inf
                for node in area.nodes:
                    if node.location is None:
                        continue
                    min_x = min(min_x, node.location.x)
                    min_y = min(min_y, node.location.y)
                    max_x = max(max_x, node.location.x)
                    max_y = max(max_y, node.location.y)

            scale = min(canvas_width / max(max_x - min_x, 1),
                        canvas_height / max(max_y - min_y, 1))

            def scale_point(x, y):
                return QPointF(scale * (x - min_x), scale * (max_y - y))

            if "polygon" in area.extra:
                points = [
                    scale_point(*p)
                    for p in area.extra["polygon"]
                ]
                painter.drawPolygon(points, QtGui.Qt.FillRule.OddEvenFill)

            brush = painter.brush()
            brush.setStyle(QtGui.Qt.BrushStyle.SolidPattern)

            for node in area.nodes:
                if node.location is None:
                    continue

                brush.setColor(_color_for_node.get(type(node), QtGui.Qt.yellow))
                painter.setBrush(brush)

                p = scale_point(node.location.x, node.location.y)
                if self.highlighted_node == node:
                    painter.drawEllipse(p, 7, 7)
                painter.drawEllipse(p, 5, 5)
                centeredText(p + QPointF(0, 15), node.name)

