import functools
import math
import os
from typing import Optional, Type, NamedTuple, Union

from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtCore import QPointF, QRectF, QSizeF, Signal

from randovania.game_description.world.area import Area
from randovania.game_description.world.node import GenericNode, DockNode, TeleporterNode, PickupNode, EventNode, Node, \
    NodeLocation
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame

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

    @classmethod
    def from_bounds(cls, data: dict[str, float]) -> "BoundsFloat":
        return BoundsFloat(data["x1"], data["y1"], data["x2"], data["y2"])

    @property
    def as_rect(self) -> QRectF:
        return QRectF(QPointF(self.min_x, self.min_y),
                      QPointF(self.max_x, self.max_y))


def centered_text(painter: QtGui.QPainter, pos: QPointF, text: str):
    rect = QRectF(pos.x() - 32767 * 0.5, pos.y() - 32767 * 0.5, 32767, 32767)
    painter.drawText(rect, QtGui.Qt.AlignCenter, text)


class DataEditorCanvas(QtWidgets.QWidget):
    game: Optional[RandovaniaGame] = None
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
    MoveNodeRequest = Signal(Node, NodeLocation)
    SelectNodeRequest = Signal(Node)
    SelectAreaRequest = Signal(Area)
    CreateDockRequest = Signal(NodeLocation, Area)

    def __init__(self):
        super().__init__()

        self._show_all_connections_action = QtWidgets.QAction("Show all node connections", self)
        self._show_all_connections_action.setCheckable(True)
        self._show_all_connections_action.setChecked(False)
        self._show_all_connections_action.triggered.connect(self.update)

        self._create_node_action = QtWidgets.QAction("Create node here", self)
        self._create_node_action.triggered.connect(self._on_create_node)

        self._move_node_action = QtWidgets.QAction("Move selected node here", self)
        self._move_node_action.triggered.connect(self._on_move_node)

    def _on_create_node(self):
        self.CreateNodeRequest.emit(self._next_node_location)

    def _on_move_node(self):
        self.MoveNodeRequest.emit(self.highlighted_node, self._next_node_location)

    def select_game(self, game: RandovaniaGame):
        self.game = game

    def select_world(self, world: World):
        self.world = world
        image_path = self.game.data_path.joinpath("assets", "maps", f"{world.name}.png") if self.game is not None else None
        if image_path is not None and image_path.exists():
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
        menu.addAction(self._show_all_connections_action)
        menu.addAction(self._create_node_action)
        menu.addAction(self._move_node_action)
        self._move_node_action.setEnabled(self.highlighted_node is not None)
        if self.highlighted_node is not None:
            self._move_node_action.setText(f"Move {self.highlighted_node.name} here")

        reference_position = self.game_loc_to_qt_local(self._next_node_location)

        # Areas Menu
        menu.addSeparator()
        has_nearby_area = False
        for area in self.world.areas:
            if "total_boundings" not in area.extra or area == self.area:
                continue

            bounds = BoundsFloat.from_bounds(area.extra["total_boundings"])
            tl = self.game_loc_to_qt_local([bounds.min_x, bounds.min_y])
            br = self.game_loc_to_qt_local([bounds.max_x, bounds.max_y])
            rect = QRectF(tl, br)
            if rect.contains(reference_position):
                a = QtWidgets.QMenu(area.name, self)
                a.addAction("View area").triggered.connect(functools.partial(self.SelectAreaRequest.emit, area))
                a.addAction("Create dock here to this area").triggered.connect(
                    functools.partial(self.CreateDockRequest.emit, self._next_node_location, area)
                )
                menu.addMenu(a)
                has_nearby_area = True

        if not has_nearby_area:
            a = QtWidgets.QAction("No areas here", self)
            a.setEnabled(False)
            menu.addAction(a)

        # Nodes Menu
        menu.addSeparator()
        has_nearby_node = False
        for node in self.area.nodes:
            if node.location is not None and (
                    self.game_loc_to_qt_local(node.location) - reference_position).manhattanLength() < 10:
                a = QtWidgets.QAction(f"Select: {node.name}", self)
                a.triggered.connect(functools.partial(self.SelectNodeRequest.emit, node))
                menu.addAction(a)
                has_nearby_node = True

        if not has_nearby_node:
            a = QtWidgets.QAction("No nodes here", self)
            a.setEnabled(False)
            menu.addAction(a)

        # Done

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

        def draw_connections_from(source_node: Node):
            if source_node.location is None:
                return

            for target_node in area.connections[source_node].keys():
                if target_node.location is None:
                    continue

                source = self.game_loc_to_qt_local(source_node.location)
                target = self.game_loc_to_qt_local(target_node.location)
                line = QtCore.QLineF(source, target)
                line_len = line.length()
                end_point = line.pointAt(1 - 7 / line_len)
                line.setPoints(end_point, line.pointAt(5 / line_len))
                painter.drawLine(line)

                line_angle = line.angle()
                line.setAngle(line_angle + 30)
                tri_point_1 = line.pointAt(15 / line_len)
                line.setAngle(line_angle - 30)
                tri_point_2 = line.pointAt(15 / line_len)

                arrow = QtGui.QPolygonF([
                    end_point,
                    tri_point_1,
                    tri_point_2
                ])
                painter.drawPolygon(arrow)

        brush = painter.brush()
        brush.setStyle(QtGui.Qt.BrushStyle.SolidPattern)
        painter.setBrush(brush)
        painter.setPen(QtGui.Qt.gray)

        if self._show_all_connections_action.isChecked():
            for node in area.nodes:
                if node != self.highlighted_node:
                    draw_connections_from(node)

        painter.setPen(QtGui.Qt.white)

        if self.highlighted_node is not None and self.highlighted_node in area.nodes:
            draw_connections_from(self.highlighted_node)

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
