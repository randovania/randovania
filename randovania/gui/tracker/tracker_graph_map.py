from __future__ import annotations

from typing import TYPE_CHECKING, Self, override

from PySide6 import QtWidgets

from randovania.gui.tracker.tracker_component import TrackerComponent
from randovania.gui.tracker.tracker_graph_map_widget import MatplotlibWidget

if TYPE_CHECKING:
    from randovania.game_description.db.region import Region
    from randovania.game_description.game_description import GameDescription
    from randovania.graph.world_graph import WorldGraph
    from randovania.gui.tracker.tracker_component import TrackerComponentSetup
    from randovania.gui.tracker.tracker_state import TrackerState


class TrackerGraphMap(TrackerComponent):
    """Draws the areas of a region as a graph, with an edge for every connection currently traversable."""

    _last_state: TrackerState | None = None
    _is_shown: bool = False

    @classmethod
    @override
    def create_for(cls, setup: TrackerComponentSetup) -> Self | None:
        return cls(setup.game_description, setup.graph)

    def __init__(self, game_description: GameDescription, graph: WorldGraph) -> None:
        super().__init__()
        self.game_description = game_description
        self.graph = graph

        self.setWindowTitle("Graph Map")

        self.root_widget = QtWidgets.QWidget()
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.setWidget(self.root_widget)

        self.graph_map_region_combo = QtWidgets.QComboBox(self.root_widget)
        self.root_layout.addWidget(self.graph_map_region_combo)

        self.matplot_widget = MatplotlibWidget(self.root_widget, game_description.region_list)
        self.root_layout.addWidget(self.matplot_widget)

        for region in game_description.region_list.regions:
            self.graph_map_region_combo.addItem(region.name, region)

        self.graph_map_region_combo.currentIndexChanged.connect(self._update_matplot_widget)
        self.visibilityChanged.connect(self._on_visibility_changed)

    def _on_visibility_changed(self, visible: bool) -> None:
        # QDockWidget.isVisible() is True even for a tabified dock sitting behind another tab
        # so we track it manually via this signal - Qt emits it both for show/hide and for tab selection.
        self._is_shown = visible
        if visible:
            self._update_matplot_widget()

    def _update_matplot_widget(self) -> None:
        # Drawing the graph is expensive, so only do it while the user can actually see it.
        if self._last_state is None or not self._is_shown:
            return

        self.matplot_widget.update_for(
            self.graph_map_region_combo.currentData(),
            self._last_state.state,
            self._last_state.nodes_in_reach,
            self.graph,
        )

    # Tracker Component

    @override
    def tracker_update(self, tracker_state: TrackerState) -> None:
        self._last_state = tracker_state
        self._update_matplot_widget()

    @override
    def focus_on_region(self, region: Region) -> None:
        self.graph_map_region_combo.setCurrentIndex(self.graph_map_region_combo.findData(region))
