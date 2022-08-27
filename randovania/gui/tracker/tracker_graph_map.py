from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6 import QtWidgets

from randovania.gui.tracker.tracker_component import TrackerComponent
from randovania.gui.tracker.tracker_graph_map_widget import MatplotlibWidget

if TYPE_CHECKING:
    from randovania.game_description.db.region import Region
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.tracker.tracker_state import TrackerState
    from randovania.resolver.state import State


class TrackerGraphMap(TrackerComponent):
    _last_state: TrackerState

    def __init__(self, game_description: GameDescription):
        super().__init__()
        self.game_description = game_description

        self.setWindowTitle("Graph Map")

        self.root_widget = QtWidgets.QWidget()
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)
        self.setWidget(self.root_widget)

        self.graph_map_region_combo = QtWidgets.QComboBox(self)
        self.graph_map_region_combo.setObjectName("graph_map_region_combo")
        self.root_layout.addWidget(self.graph_map_region_combo)

        self.matplot_widget = MatplotlibWidget(self, self.game_description.region_list)
        self.root_layout.addWidget(self.matplot_widget)

        for region in self.game_description.region_list.regions:
            self.graph_map_region_combo.addItem(region.name, region)
        self.graph_map_region_combo.currentIndexChanged.connect(self.on_graph_map_region_combo)

    def on_graph_map_region_combo(self):
        self._update_matplot_widget()

    def _update_matplot_widget(self):
        self.matplot_widget.update_for(
            self.graph_map_region_combo.currentData(),
            self._last_state.state,
            self._last_state.nodes_in_reach,
        )

    # Tracker Component

    def reset(self):
        pass

    def decode_persisted_state(self, previous_state: dict) -> Any | None:
        return True

    def apply_previous_state(self, previous_state: Any) -> None:
        pass

    def persist_current_state(self) -> dict:
        return {}

    def fill_into_state(self, state: State):
        pass

    def tracker_update(self, tracker_state: TrackerState):
        self._last_state = tracker_state
        # TODO: check if shown
        self._update_matplot_widget()

    def focus_on_region(self, region: Region):
        self.graph_map_region_combo.setCurrentIndex(self.graph_map_region_combo.findData(region))
