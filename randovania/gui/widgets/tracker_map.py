from __future__ import annotations

import collections
import logging
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import networkx
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6 import QtWidgets

from randovania.game_description.db.dock_node import DockNode

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.region import Region
    from randovania.game_description.db.region_list import RegionList
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode


class MatplotlibWidget(QtWidgets.QWidget):
    ax: Axes

    def __init__(self, parent: QtWidgets.QWidget, region_list: RegionList):
        super().__init__(parent)

        self.region_list = region_list

        fig = Figure(figsize=(7, 5), dpi=65, facecolor=(1, 1, 1), edgecolor=(0, 0, 0))
        self.canvas = FigureCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.toolbar)
        lay.addWidget(self.canvas)

        self.ax = fig.add_subplot(111)
        self.line, *_ = self.ax.plot([])

        self._region_to_node_positions: dict[str, dict] = {}

    def _positions_for_region(self, region: Region, state: State) -> dict:
        g = networkx.DiGraph()

        for area in region.areas:
            g.add_node(area)

        for area in region.areas:
            nearby_areas = set()
            for node in area.nodes:
                if isinstance(node, DockNode):
                    try:
                        target_node = self.region_list.resolve_dock_node(node, state.patches)
                        nearby_areas.add(self.region_list.nodes_to_area(target_node))
                    except IndexError as e:
                        logging.error(f"For {node.name} in {area.name}, received {e}")
                        continue
            for other_area in nearby_areas:
                g.add_edge(area, other_area)

        return networkx.drawing.spring_layout(g)

    def update_for(self, region: Region, state: State, nodes_in_reach: list[WorldGraphNode], graph: WorldGraph) -> None:
        g = networkx.DiGraph()

        for area in region.areas:
            g.add_node(area)

        nearby_areas_by_area: dict[Area, set[Area]] = collections.defaultdict(set)

        for node in nodes_in_reach:
            if node.area not in region.areas:
                continue

            for connection in node.connections:
                target = graph.nodes[connection.target]
                if target.area is node.area or target.area not in region.areas:
                    continue

                if connection.requirement.satisfied(state.resources, state.health_for_damage_requirements):
                    nearby_areas_by_area[node.area].add(target.area)

        for source_area, area_list in nearby_areas_by_area.items():
            for target_area in area_list:
                g.add_edge(source_area, target_area)

        self.ax.clear()

        cf = self.ax.get_figure()
        assert cf is not None
        cf.set_facecolor("w")

        if region.name not in self._region_to_node_positions:
            self._region_to_node_positions[region.name] = self._positions_for_region(region, state)
        pos = self._region_to_node_positions[region.name]

        networkx.draw_networkx_nodes(g, pos, ax=self.ax)
        networkx.draw_networkx_edges(g, pos, arrows=True, ax=self.ax)
        networkx.draw_networkx_labels(
            g, pos, ax=self.ax, labels={area: area.name for area in region.areas}, verticalalignment="top"
        )

        self.ax.set_axis_off()

        plt.draw_if_interactive()
        self.canvas.draw()
