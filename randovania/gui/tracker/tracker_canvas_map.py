from __future__ import annotations

import typing
from typing import TYPE_CHECKING, Self, override

from PySide6 import QtWidgets

from randovania.gui.lib import signal_handling
from randovania.gui.tracker.tracker_component import TrackerComponent
from randovania.gui.widgets.data_editor_canvas import DataEditorCanvas

if TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region import Region
    from randovania.game_description.game_description import GameDescription
    from randovania.graph.world_graph import WorldGraph
    from randovania.gui.tracker.tracker_component import TrackerComponentSetup
    from randovania.gui.tracker.tracker_state import TrackerState


class TrackerCanvasMap(TrackerComponent):
    """Draws the currently selected area, using the same canvas as the Data Visualizer."""

    @classmethod
    @override
    def create_for(cls, setup: TrackerComponentSetup) -> Self | None:
        if setup.game_description.game.gui.hide_database_map_view:
            return None

        return cls(setup.game_description, setup.graph)

    def __init__(self, game_description: GameDescription, graph: WorldGraph) -> None:
        super().__init__()
        self.game_description = game_description
        self.graph = graph

        self.setWindowTitle("Map")

        self.root_widget = QtWidgets.QWidget()
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)
        self.root_layout.setContentsMargins(2, 2, 2, 2)
        self.setWidget(self.root_widget)

        self.map_area_layout = QtWidgets.QHBoxLayout()
        self.root_layout.addLayout(self.map_area_layout)

        self.map_region_combo = QtWidgets.QComboBox(self.root_widget)
        self.map_area_layout.addWidget(self.map_region_combo)

        self.map_area_combo = QtWidgets.QComboBox(self.root_widget)
        self.map_area_layout.addWidget(self.map_area_combo)

        self.map_canvas = DataEditorCanvas(self.root_widget)
        self.root_layout.addWidget(self.map_canvas)

        self.map_canvas.select_game(graph.game_enum)
        self.map_canvas.set_world_graph(graph)

        for region in sorted(game_description.region_list.regions, key=lambda x: x.name):
            self.map_region_combo.addItem(region.name, userData=region)

        self.on_map_region_combo(0)
        self.map_region_combo.currentIndexChanged.connect(self.on_map_region_combo)
        self.map_area_combo.currentIndexChanged.connect(self.on_map_area_combo)
        self.map_canvas.set_edit_mode(False)
        self.map_canvas.SelectAreaRequest.connect(self.focus_on_area)
        self.map_canvas.SelectNodeRequest.connect(self._on_map_select_node)

    def on_map_region_combo(self, _: typing.Any) -> None:
        region: Region = self.map_region_combo.currentData()
        self.map_area_combo.clear()
        for area in sorted(region.areas, key=lambda x: x.name):
            self.map_area_combo.addItem(area.name, userData=area)

        self.map_canvas.select_region(region)
        self.on_map_area_combo(0)

    def on_map_area_combo(self, _: typing.Any) -> None:
        area: Area = self.map_area_combo.currentData()
        self.map_canvas.select_area(area)

    def _on_map_select_node(self, node: Node) -> None:
        self.ActionRequested.emit(self.graph.original_to_node[node.node_index])

    # Tracker Component

    @override
    def tracker_update(self, tracker_state: TrackerState) -> None:
        self.map_canvas.set_state(tracker_state.state)
        self.map_canvas.set_visible_nodes(
            {node.database_node for node in tracker_state.nodes_in_reach if node.database_node is not None}
        )

    @override
    def focus_on_region(self, region: Region) -> None:
        signal_handling.set_combo_with_value(self.map_region_combo, region)
        self.on_map_region_combo(0)

    @override
    def focus_on_area(self, area: Area) -> None:
        signal_handling.set_combo_with_value(self.map_area_combo, area)
