from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6 import QtWidgets

from randovania.gui.lib import signal_handling
from randovania.gui.lib.data_editor_canvas import DataEditorCanvas
from randovania.gui.tracker.tracker_component import TrackerComponent

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.world.area import Area
    from randovania.game_description.world.world import World
    from randovania.generator.filler.runner import PlayerPool
    from randovania.gui.tracker.tracker_state import TrackerState
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.state import State


class TrackerCanvasMap(TrackerComponent):

    @classmethod
    def create_for(cls, player_pool: PlayerPool, configuration: BaseConfiguration) -> TrackerCanvasMap:
        return cls(player_pool.game)

    def __init__(self, game_description: GameDescription):
        super().__init__()
        self.game_description = game_description

        self.setWindowTitle("Map")

        self.root_widget = QtWidgets.QWidget()
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)
        self.setWidget(self.root_widget)

        # World/Area selector
        self.map_area_layout = QtWidgets.QHBoxLayout()
        self.root_layout.addLayout(self.map_area_layout)

        self.map_world_combo = QtWidgets.QComboBox(self.root_widget)
        self.map_world_combo.setObjectName("map_world_combo")
        self.map_area_layout.addWidget(self.map_world_combo)

        self.map_area_combo = QtWidgets.QComboBox(self.root_widget)
        self.map_area_combo.setObjectName("map_area_combo")
        self.map_area_layout.addWidget(self.map_area_combo)

        # Map
        self.map_canvas = DataEditorCanvas(self.root_widget)
        self.map_canvas.setObjectName("map_canvas")
        self.root_layout.addWidget(self.map_canvas)
        self.map_canvas.select_game(self.game_description.game)

        # Connect
        for world in sorted(self.game_description.world_list.worlds, key=lambda x: x.name):
            self.map_world_combo.addItem(world.name, userData=world)

        self.on_map_world_combo(0)
        self.map_world_combo.currentIndexChanged.connect(self.on_map_world_combo)
        self.map_area_combo.currentIndexChanged.connect(self.on_map_area_combo)
        self.map_canvas.set_edit_mode(False)
        self.map_canvas.SelectAreaRequest.connect(self.focus_on_area)

    # Events

    def on_map_world_combo(self, _):
        world: World = self.map_world_combo.currentData()
        self.map_area_combo.clear()
        for area in sorted(world.areas, key=lambda x: x.name):
            self.map_area_combo.addItem(area.name, userData=area)

        self.map_canvas.select_world(world)
        self.on_map_area_combo(0)

    def on_map_area_combo(self, _):
        area: Area = self.map_area_combo.currentData()
        self.map_canvas.select_area(area)

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
        self.map_canvas.set_state(tracker_state.state)
        self.map_canvas.set_visible_nodes(set(tracker_state.nodes_in_reach))

    def focus_on_world(self, world: World):
        signal_handling.set_combo_with_value(self.map_world_combo, world)
        self.on_map_world_combo(0)

    def focus_on_area(self, area: Area):
        signal_handling.set_combo_with_value(self.map_area_combo, area)
