from __future__ import annotations

import collections
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.gui.tracker.tracker_component import TrackerComponent
from randovania.layout.lib.teleporters import TeleporterConfiguration, TeleporterShuffleMode
from randovania.patching.prime import elevators

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.state import State


class TrackerElevatorsWidget(QtWidgets.QDockWidget, TrackerComponent):
    _elevator_id_to_combo: dict[NodeIdentifier, QtWidgets.QComboBox]

    @classmethod
    def create_for(cls, game_description: GameDescription, configuration: BaseConfiguration,
                   ) -> TrackerElevatorsWidget | None:

        if not hasattr(configuration, "elevators"):
            return None

        elevators_config = getattr(configuration, "elevators")
        assert isinstance(elevators_config, TeleporterConfiguration)

        return cls(game_description, elevators_config)

    def __init__(self, game_description: GameDescription, elevators_config: TeleporterConfiguration):
        super().__init__()
        self.game = game_description.game
        self.game_description = game_description

        self._elevator_id_to_combo = {}

        self.setWindowTitle("Elevators")

        self.root_widget = QtWidgets.QScrollArea()
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)
        self.root_widget.setWidgetResizable(True)
        self.setWidget(self.root_widget)

        self.scroll_contents = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QGridLayout(self.scroll_contents)
        self.root_widget.setWidget(self.scroll_contents)

        region_list = self.game_description.region_list
        nodes_by_region: dict[str, list[DockNode]] = collections.defaultdict(list)

        targets = {}
        teleporter_dock_types = self.game_description.dock_weakness_database.all_teleporter_dock_types
        for region, area, node in region_list.all_regions_areas_nodes:
            if isinstance(node, DockNode) and node.dock_type in teleporter_dock_types:
                name = region.correct_name(area.in_dark_aether)
                nodes_by_region[name].append(node)

                location = AreaIdentifier(region.name, area.name)
                targets[elevators.get_short_elevator_or_area_name(elevators_config.game, region_list, location,
                                                                  True)] = location

        if elevators_config.mode == TeleporterShuffleMode.ONE_WAY_ANYTHING:
            targets = {}
            for region in region_list.regions:
                for area in region.areas:
                    name = region.correct_name(area.in_dark_aether)
                    targets[f"{name} - {area.name}"] = AreaIdentifier(region.name, area.name)

        combo_targets = sorted(targets.items(), key=lambda it: it[0])

        for region_name in sorted(nodes_by_region.keys()):
            nodes = nodes_by_region[region_name]
            nodes_locations = [region_list.identifier_for_node(node).area_location
                               for node in nodes]
            nodes_names = [elevators.get_short_elevator_or_area_name(elevators_config.game, region_list,
                                                                     location, False)
                           for location in nodes_locations]

            group = QtWidgets.QGroupBox(self.scroll_contents)
            group.setTitle(region_name)
            self.scroll_layout.addWidget(group)
            layout = QtWidgets.QGridLayout(group)

            for i, (node, location, name) in enumerate(sorted(zip(nodes, nodes_locations, nodes_names),
                                                              key=lambda it: it[2])):
                node_name = QtWidgets.QLabel(group)
                node_name.setText(name)
                node_name.setWordWrap(True)
                node_name.setMinimumWidth(75)
                layout.addWidget(node_name, i, 0)

                combo = QtWidgets.QComboBox(group)
                if elevators_config.is_vanilla:
                    combo.addItem("Vanilla", node.default_connection)
                    combo.setEnabled(False)
                else:
                    combo.addItem("Undefined", None)
                    for target_name, connection in combo_targets:
                        combo.addItem(target_name, connection)

                combo.setMinimumContentsLength(11)
                # combo.currentIndexChanged.connect(self.update_locations_tree_for_reachable_nodes)
                self._elevator_id_to_combo[region_list.identifier_for_node(node)] = combo
                layout.addWidget(combo, i, 1)

    def apply_previous_state(self, previous_state: dict) -> bool:
        try:
            teleporters: dict[NodeIdentifier, AreaIdentifier | None] = {
                NodeIdentifier.from_json(item["teleporter"]): (
                    AreaIdentifier.from_json(item["data"])
                    if item["data"] is not None else None
                )
                for item in previous_state["elevators"]
            }
        except (KeyError, AttributeError):
            return False

        for teleporter, area_location in teleporters.items():
            combo = self._elevator_id_to_combo[teleporter]
            if area_location is None:
                combo.setCurrentIndex(0)
                continue
            for i in range(combo.count()):
                if area_location == combo.itemData(i):
                    combo.setCurrentIndex(i)
                    break

        return True

    def reset(self):
        for elevator in self._elevator_id_to_combo.values():
            elevator.setCurrentIndex(0)

    def persist_current_state(self) -> dict:
        return {
            "elevators": [
                {
                    "teleporter": teleporter.as_json,
                    "data": combo.currentData().as_json if combo.currentIndex() > 0 else None
                }
                for teleporter, combo in self._elevator_id_to_combo.items()
            ],
        }

    def fill_into_state(self, state: State) -> State | None:
        region_list = state.region_list
        state.patches = state.patches.assign_dock_connections(
            (region_list.typed_node_by_identifier(teleporter, DockNode),
             region_list.default_node_for_area(combo.currentData()))
            for teleporter, combo in self._elevator_id_to_combo.items() if combo.currentData() is not None
        )

        return state
