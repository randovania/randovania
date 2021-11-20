import math
import os
from typing import Optional, Type

from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import QPointF, QRectF

from randovania import get_data_path
from randovania.game_description.world.area import Area
from randovania.game_description.world.node import GenericNode, DockNode, TeleporterNode, PickupNode, EventNode, Node
from randovania.game_description.world.world import World

_color_for_node: dict[Type[Node], int] = {
    GenericNode: QtGui.Qt.red,
    DockNode: QtGui.Qt.green,
    TeleporterNode: QtGui.Qt.blue,
    PickupNode: QtGui.Qt.cyan,
    EventNode: QtGui.Qt.magenta,
}


class DataEditorCanvas(QtWidgets.QWidget):
    world: Optional[World] = None
    area: Optional[Area] = None
    highlighted_node: Optional[Node] = None
    _background_image: Optional[QtGui.QImage] = None
    world_min_x: float
    world_min_y: float
    world_max_x: float
    world_max_y: float
    image_min_x: int
    image_min_y: int
    image_max_x: int
    image_max_y: int

    def select_world(self, world: World):
        self.world = world
        image_path = get_data_path().joinpath("gui_assets", "dread_maps", f"{world.name}.png")
        if image_path.exists():
            self._background_image = QtGui.QImage(os.fspath(image_path))
            self.image_min_x = world.extra.get("map_min_x", 0)
            self.image_max_x = self._background_image.width() - world.extra.get("map_max_x", 0)
            self.image_min_y = world.extra.get("map_min_y", 0)
            self.image_max_y = self._background_image.height() - world.extra.get("map_max_y", 0)
        else:
            self._background_image = None

        min_x, min_y = math.inf, math.inf
        max_x, max_y = -math.inf, -math.inf

        for area in world.areas:
            total_boundings = area.extra.get("total_boundings")
            if total_boundings is None:
                continue
            min_x = min(min_x, total_boundings["x1"], total_boundings["x2"])
            max_x = max(max_x, total_boundings["x1"], total_boundings["x2"])
            min_y = min(min_y, total_boundings["y1"], total_boundings["y2"])
            max_y = max(max_y, total_boundings["y1"], total_boundings["y2"])

        self.world_min_x = min_x
        self.world_max_x = max_x
        self.world_min_y = min_y
        self.world_max_y = max_y
        self.update()

    def get_image_point(self, x: float, y: float):
        return QPointF(self.image_min_x + (self.image_max_x - self.image_min_x) * x,
                       self.image_min_y + (self.image_max_y - self.image_min_y) * y)

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

            area_width = max(max_x - min_x, 1)
            area_height = max(max_y - min_y, 1)
            scale = min(canvas_width / area_width, canvas_height / area_height)
            if scale == 0:
                return

            # Center what we're drawing
            painter.translate(
                (canvas_width - area_width * scale) / 2,
                (canvas_height - area_height * scale) / 2,
            )

            scaled_border = border / scale

            # Calculate the top-left corner and bottom-right of the background image
            percent_x_start = (min_x - self.world_min_x - scaled_border) / (self.world_max_x - self.world_min_x)
            percent_x_end = (max_x - self.world_min_x + scaled_border) / (self.world_max_x - self.world_min_x)
            percent_y_start = 1 - (max_y - self.world_min_y + scaled_border) / (self.world_max_y - self.world_min_y)
            percent_y_end = 1 - (min_y - self.world_min_y - scaled_border) / (self.world_max_y - self.world_min_y)

            if self._background_image is not None:
                painter.drawImage(
                    QRectF(-border, -border,
                           border * 2 + area_width * scale,
                           border * 2 + area_height * scale),
                    self._background_image,
                    QRectF(self.get_image_point(percent_x_start, percent_y_start),
                           self.get_image_point(percent_x_end, percent_y_end)))

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

            if (self.highlighted_node is not None and self.highlighted_node in area.nodes
                    and self.highlighted_node.location is not None):
                for node in area.connections[self.highlighted_node].keys():
                    if node.location is None:
                        continue
                    painter.drawLine(scale_point(self.highlighted_node.location.x, self.highlighted_node.location.y),
                                     scale_point(node.location.x, node.location.y))
