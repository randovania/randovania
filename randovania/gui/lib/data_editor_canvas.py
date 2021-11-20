import math
import os
from typing import Optional, Type, NamedTuple, Union

from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import QPointF, QRectF, QSizeF, Signal

from randovania import get_data_path
from randovania.game_description.world.area import Area
from randovania.game_description.world.node import GenericNode, DockNode, TeleporterNode, PickupNode, EventNode, Node, \
    NodeLocation
from randovania.game_description.world.world import World

_color_for_node: dict[Type[Node], int] = {
    GenericNode: QtGui.Qt.red,
    DockNode: QtGui.Qt.green,
    TeleporterNode: QtGui.Qt.blue,
    PickupNode: QtGui.Qt.cyan,
    EventNode: QtGui.Qt.magenta,
}


class BoundsInt(NamedTuple):
    min_x: int
    min_y: int
    max_x: int
    max_y: int


class BoundsFloat(NamedTuple):
    min_x: float
    min_y: float
    max_x: float
    max_y: float


def centered_text(painter: QtGui.QPainter, pos: QPointF, text: str):
    rect = QRectF(pos.x() - 32767 * 0.5, pos.y() - 32767 * 0.5, 32767, 32767)
    painter.drawText(rect, QtGui.Qt.AlignCenter, text)


class DataEditorCanvas(QtWidgets.QWidget):
    world: Optional[World] = None
    area: Optional[Area] = None
    highlighted_node: Optional[Node] = None
    _background_image: Optional[QtGui.QImage] = None
    world_bounds: BoundsFloat
    area_bounds: BoundsFloat
    area_size: QSizeF
    image_bounds: BoundsInt

    scale: float
    border_x: float = 75
    border_y: float = 75
    canvas_size: QSizeF

    _next_node_location: NodeLocation = NodeLocation(0, 0, 0)
    CreateNodeRequest = Signal(NodeLocation)

    def __init__(self):
        super().__init__()

        self._create_node_action = QtWidgets.QAction("Create node here", self)
        self._create_node_action.triggered.connect(self._on_create_node)

    def _on_create_node(self):
        self.CreateNodeRequest.emit(self._next_node_location)

    def select_world(self, world: World):
        self.world = world
        image_path = get_data_path().joinpath("gui_assets", "dread_maps", f"{world.name}.png")
        if image_path.exists():
            self._background_image = QtGui.QImage(os.fspath(image_path))
            self.image_bounds = BoundsInt(
                min_x=world.extra.get("map_min_x", 0),
                min_y=world.extra.get("map_min_y", 0),
                max_x=self._background_image.width() - world.extra.get("map_max_x", 0),
                max_y=self._background_image.height() - world.extra.get("map_max_y", 0),
            )
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

        self.world_bounds = BoundsFloat(
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
        )
        self.update()

    def get_image_point(self, x: float, y: float):
        bounds = self.image_bounds
        return QPointF(bounds.min_x + (bounds.max_x - bounds.min_x) * x,
                       bounds.min_y + (bounds.max_y - bounds.min_y) * y)

    def select_area(self, area: Optional[Area]):
        self.area = area
        if area is None:
            return

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

        self.area_bounds = BoundsFloat(
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
        )
        self.area_size = QSizeF(
            max(max_x - min_x, 1),
            max(max_y - min_y, 1),
        )
        self.update()

    def highlight_node(self, node: Node):
        self.highlighted_node = node
        self.update()

    def _update_scale_variables(self):
        self.border_x = self.rect().width() * 0.05
        self.border_y = self.rect().height() * 0.05
        canvas_width = max(self.rect().width() - self.border_x * 2, 1)
        canvas_height = max(self.rect().height() - self.border_y * 2, 1)

        self.scale = min(canvas_width / self.area_size.width(),
                         canvas_height / self.area_size.height())

        self.canvas_size = QSizeF(canvas_width, canvas_width)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        local_pos = QPointF(self.mapFromGlobal(event.globalPos()))
        local_pos -= self.get_area_canvas_offset()
        self._next_node_location = self.qt_local_to_game_loc(local_pos)

        menu = QtWidgets.QMenu(self)
        menu.addAction(self._create_node_action)
        menu.exec_(event.globalPos())

    def game_loc_to_qt_local(self, pos: Union[NodeLocation, list[float]]) -> QPointF:
        if isinstance(pos, NodeLocation):
            x = pos.x
            y = pos.y
        else:
            x, y = pos[0], pos[1]

        return QPointF(self.scale * (x - self.area_bounds.min_x), self.scale * (self.area_bounds.max_y - y))

    def qt_local_to_game_loc(self, pos: QPointF) -> NodeLocation:
        return NodeLocation((pos.x() / self.scale) + self.area_bounds.min_x,
                            self.area_bounds.max_y - (pos.y() / self.scale),
                            0)

    def get_area_canvas_offset(self):
        return QPointF(
            (self.width() - self.area_size.width() * self.scale) / 2,
            (self.height() - self.area_size.height() * self.scale) / 2,
        )

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        if self.world is None or self.area is None:
            return

        self._update_scale_variables()

        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.Qt.white)
        painter.setFont(QtGui.QFont("Arial", 10))

        # Center what we're drawing
        painter.translate(self.get_area_canvas_offset())

        if self._background_image is not None:
            scaled_border_x = 8 * self.border_x / self.scale
            scaled_border_y = 8 * self.border_y / self.scale

            wbounds = self.world_bounds
            abounds = self.area_bounds

            # Calculate the top-left corner and bottom-right of the background image
            percent_x_start = (abounds.min_x - wbounds.min_x - scaled_border_x) / (wbounds.max_x - wbounds.min_x)
            percent_x_end = (abounds.max_x - wbounds.min_x + scaled_border_x) / (wbounds.max_x - wbounds.min_x)
            percent_y_start = 1 - (abounds.max_y - wbounds.min_y + scaled_border_y) / (wbounds.max_y - wbounds.min_y)
            percent_y_end = 1 - (abounds.min_y - wbounds.min_y - scaled_border_y) / (wbounds.max_y - wbounds.min_y)

            painter.drawImage(
                QRectF(-scaled_border_x * self.scale,
                       -scaled_border_y * self.scale,
                       (scaled_border_x * 2 + self.area_size.width()) * self.scale,
                       (scaled_border_y * 2 + self.area_size.height()) * self.scale),
                self._background_image,
                QRectF(self.get_image_point(percent_x_start, percent_y_start),
                       self.get_image_point(percent_x_end, percent_y_end)))

        area = self.area
        if "polygon" in area.extra:
            points = [
                self.game_loc_to_qt_local(p)
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

            p = self.game_loc_to_qt_local(node.location)
            if self.highlighted_node == node:
                painter.drawEllipse(p, 7, 7)
            painter.drawEllipse(p, 5, 5)
            centered_text(painter, p + QPointF(0, 15), node.name)

        if (self.highlighted_node is not None and self.highlighted_node in area.nodes
                and self.highlighted_node.location is not None):

            for node in area.connections[self.highlighted_node].keys():
                if node.location is None:
                    continue
                painter.drawLine(
                    self.game_loc_to_qt_local(self.highlighted_node.location),
                    self.game_loc_to_qt_local(node.location))
