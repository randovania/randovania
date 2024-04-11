from __future__ import annotations

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

    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region import Region
    from randovania.game_description.db.region_list import RegionList
    from randovania.resolver.state import State


class MatplotlibWidget(QtWidgets.QWidget):
    ax: Axes

    def __init__(self, parent, region_list: RegionList):
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

        self._region_to_node_positions = {}

    def _positions_for_region(self, region: Region, state: State):
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

    def update_for(self, region: Region, state: State, nodes_in_reach: set[Node]):
        g = networkx.DiGraph()

        for area in region.areas:
            g.add_node(area)

        context = state.node_context()
        for area in region.areas:
            nearby_areas = set()
            for node in area.nodes:
                if node not in nodes_in_reach:
                    continue

                for other_node, requirement in node.connections_from(context):
                    if requirement.satisfied(context, state.energy):
                        other_area = self.region_list.nodes_to_area(other_node)
                        if other_area in region.areas:
                            nearby_areas.add(other_area)

            for other_area in nearby_areas:
                g.add_edge(area, other_area)

        self.ax.clear()

        cf = self.ax.get_figure()
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
