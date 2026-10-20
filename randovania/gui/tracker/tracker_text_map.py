from __future__ import annotations

import typing
from typing import TYPE_CHECKING, Self, override

from PySide6 import QtCore, QtGui, QtWidgets

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.gui.dialog.scroll_label_dialog import ScrollLabelDialog
from randovania.gui.tracker.tracker_component import TrackerComponent
from randovania.resolver.resolver_reach import ResolverReach

if TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import NodeIndex
    from randovania.game_description.db.region import Region
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode
    from randovania.gui.tracker.tracker_component import TrackerComponentSetup
    from randovania.gui.tracker.tracker_state import TrackerState
    from randovania.resolver.logic import Logic


class TrackerTextMap(TrackerComponent):
    """Lists every node of the game as a tree, highlighting which ones are currently reachable."""

    _last_state: TrackerState | None = None
    _region_name_to_item: dict[str, QtWidgets.QTreeWidgetItem]
    _area_name_to_item: dict[tuple[str, str], QtWidgets.QTreeWidgetItem]
    _node_to_item: dict[NodeIndex, QtWidgets.QTreeWidgetItem]

    @classmethod
    @override
    def create_for(cls, setup: TrackerComponentSetup) -> Self | None:
        return cls(setup.graph, setup.logic)

    def __init__(self, graph: WorldGraph, logic: Logic) -> None:
        super().__init__()
        self.graph = graph
        self.logic = logic

        self._region_name_to_item = {}
        self._area_name_to_item = {}
        self._node_to_item = {}

        self.setWindowTitle("Text Map")

        self.root_widget = QtWidgets.QWidget()
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)
        self.root_layout.setContentsMargins(4, 4, 4, 4)
        self.setWidget(self.root_widget)

        self.resource_filter_check = QtWidgets.QCheckBox(self.root_widget)
        self.resource_filter_check.setText("Show only resources")
        self.resource_filter_check.setChecked(True)
        self.root_layout.addWidget(self.resource_filter_check)

        self.hide_collected_resources_check = QtWidgets.QCheckBox(self.root_widget)
        self.hide_collected_resources_check.setText("Hide collected resources")
        self.root_layout.addWidget(self.hide_collected_resources_check)

        self.current_location_label = QtWidgets.QLabel(self.root_widget)
        self.current_location_label.setText("Current location:")
        self.current_location_label.setWordWrap(True)
        self.root_layout.addWidget(self.current_location_label)

        self.possible_locations_tree = QtWidgets.QTreeWidget(self.root_widget)
        self.possible_locations_tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.ActionsContextMenu)
        self.possible_locations_tree.headerItem().setText(0, "Accessible Locations")
        self.root_layout.addWidget(self.possible_locations_tree)

        self.action_show_path_to_here = QtGui.QAction("Show path to here")
        self.action_show_path_to_here.triggered.connect(self._on_show_path_to_here)
        self.possible_locations_tree.itemDoubleClicked.connect(self._on_tree_node_double_clicked)
        self.possible_locations_tree.addAction(self.action_show_path_to_here)

        self._create_tree_items()

        self.resource_filter_check.stateChanged.connect(self._refresh_visible_nodes)
        self.hide_collected_resources_check.stateChanged.connect(self._refresh_visible_nodes)

    def _create_tree_items(self) -> None:
        def get_region_item(region: Region) -> QtWidgets.QTreeWidgetItem:
            if region.name not in self._region_name_to_item:
                item = QtWidgets.QTreeWidgetItem(self.possible_locations_tree)
                item.setText(0, region.name)
                item.setExpanded(True)
                self._region_name_to_item[region.name] = item
            return self._region_name_to_item[region.name]

        def get_area_item(region: Region, area: Area) -> QtWidgets.QTreeWidgetItem:
            if (region.name, area.name) not in self._area_name_to_item:
                item = QtWidgets.QTreeWidgetItem(get_region_item(region))
                item.area = area  # type: ignore[attr-defined]
                item.setText(0, area.name)
                item.setHidden(True)
                self._area_name_to_item[(region.name, area.name)] = item
            return self._area_name_to_item[(region.name, area.name)]

        for node in self.graph.nodes:
            node_item = QtWidgets.QTreeWidgetItem(get_area_item(node.region, node.area))
            node_item.setText(0, node.identifier.node)
            node_item.node = node  # type: ignore[attr-defined]
            if node.is_resource_node():
                node_item.setFlags(node_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            self._node_to_item[node.node_index] = node_item

    @property
    def _show_only_resource_nodes(self) -> bool:
        return self.resource_filter_check.isChecked()

    @property
    def _hide_collected_resources(self) -> bool:
        return self.hide_collected_resources_check.isChecked()

    @staticmethod
    def _pretty_node_name(node: WorldGraphNode) -> str:
        return f"{node.identifier.region} - {node.identifier.area} / {node.identifier.node}"

    def _on_tree_node_double_clicked(self, item: QtWidgets.QTreeWidgetItem, _: typing.Any) -> None:
        node: WorldGraphNode | None = getattr(item, "node", None)

        if not item.isDisabled() and node is not None:
            self.ActionRequested.emit(node)

    def _on_show_path_to_here(self) -> None:
        target: QtWidgets.QTreeWidgetItem | None = self.possible_locations_tree.currentItem()
        if target is None or self._last_state is None:
            return

        node: WorldGraphNode | None = getattr(target, "node", None)
        if node is not None:
            reach = ResolverReach.calculate_reach(self.logic, self._last_state.state)
            try:
                path = reach.path_to_node(node)
            except KeyError:
                path = ()

            text = [f"<p><span style='font-weight:600;'>Path to {node.name}</span></p><ul>"]
            for p in path:
                text.append(f"<li>{p.full_name()}</li>")
            text.append("</ul>")

            dialog = ScrollLabelDialog(self, "".join(text), "Path to node")
            dialog.exec_()
        else:
            QtWidgets.QMessageBox.warning(
                self, "Invalid target", f"Can't find a path to {target.text(0)}. Please select a node."
            )

    def _refresh_visible_nodes(self) -> None:
        if self._last_state is None:
            return

        state = self._last_state.state
        resources = state.resources
        indices_in_reach = self._last_state.indices_in_reach
        visible_areas: set[tuple[str, str]] = set()

        for node in self.graph.nodes:
            is_visible = node.node_index in indices_in_reach

            node_item = self._node_to_item[node.node_index]
            if node.is_resource_node():
                if self._show_only_resource_nodes:
                    is_visible = is_visible and not isinstance(node.database_node, ConfigurableNode)

                is_collected = node.has_all_resources(resources)
                is_visible = is_visible and not (self._hide_collected_resources and is_collected)

                node_item.setDisabled(
                    not (
                        not is_collected
                        and node.requirement_to_collect.satisfied(resources, state.health_for_damage_requirements)
                    )
                )
                node_item.setCheckState(
                    0, QtCore.Qt.CheckState.Checked if is_collected else QtCore.Qt.CheckState.Unchecked
                )

            elif self._show_only_resource_nodes:
                is_visible = False

            node_item.setHidden(not is_visible)
            if is_visible:
                visible_areas.add((node.region.name, node.area.name))

        for key, item in self._area_name_to_item.items():
            item.setHidden(key not in visible_areas)

    # Tracker Component

    @override
    def tracker_update(self, tracker_state: TrackerState) -> None:
        self._last_state = tracker_state
        self.current_location_label.setText(f"Current location: {self._pretty_node_name(tracker_state.actions[-1])}")
        self._refresh_visible_nodes()
