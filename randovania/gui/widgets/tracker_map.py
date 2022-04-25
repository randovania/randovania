import logging

import matplotlib.pyplot as plt
import networkx
from PySide6 import QtWidgets
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.node import Node
from randovania.game_description.world.world import World
from randovania.game_description.world.world_list import WorldList
from randovania.resolver.state import State


class MatplotlibWidget(QtWidgets.QWidget):
    ax: Axes

    def __init__(self, parent, world_list: WorldList):
        super().__init__(parent)

        self.world_list = world_list

        fig = Figure(figsize=(7, 5), dpi=65, facecolor=(1, 1, 1), edgecolor=(0, 0, 0))
        self.canvas = FigureCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.toolbar)
        lay.addWidget(self.canvas)

        self.ax = fig.add_subplot(111)
        self.line, *_ = self.ax.plot([])

        self._world_to_node_positions = {}

    def _positions_for_world(self, world: World, state: State):
        g = networkx.DiGraph()

        for area in world.areas:
            g.add_node(area)

        for area in world.areas:
            nearby_areas = set()
            for node in area.nodes:
                if isinstance(node, DockNode):
                    try:
                        target_node = self.world_list.resolve_dock_node(node, state.patches)
                        if target_node is not None:
                            nearby_areas.add(self.world_list.nodes_to_area(target_node))
                    except IndexError as e:
                        logging.error(f"For {node.name} in {area.name}, received {e}")
                        continue
            for other_area in nearby_areas:
                g.add_edge(area, other_area)

        return networkx.drawing.spring_layout(g)

    def update_for(self, world: World, state: State, nodes_in_reach: set[Node]):
        g = networkx.DiGraph()

        for area in world.areas:
            g.add_node(area)

        context = state.node_context()
        for area in world.areas:
            nearby_areas = set()
            for node in area.nodes:
                if node not in nodes_in_reach:
                    continue

                for other_node, requirement in node.connections_from(context):
                    if requirement.satisfied(state.resources, state.energy, state.resource_database):
                        other_area = self.world_list.nodes_to_area(other_node)
                        if other_area in world.areas:
                            nearby_areas.add(other_area)

            for other_area in nearby_areas:
                g.add_edge(area, other_area)

        self.ax.clear()

        cf = self.ax.get_figure()
        cf.set_facecolor("w")

        if world.name not in self._world_to_node_positions:
            self._world_to_node_positions[world.name] = self._positions_for_world(world, state)
        pos = self._world_to_node_positions[world.name]

        networkx.draw_networkx_nodes(g, pos, ax=self.ax)
        networkx.draw_networkx_edges(g, pos, arrows=True, ax=self.ax)
        networkx.draw_networkx_labels(g, pos, ax=self.ax,
                                      labels={area: area.name for area in world.areas},
                                      verticalalignment='top')

        self.ax.set_axis_off()

        plt.draw_if_interactive()
        self.canvas.draw()
