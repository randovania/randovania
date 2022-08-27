from __future__ import annotations

import typing
from typing import Any

from PySide6 import QtGui, QtWidgets
from qasync import QtCore

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.resource_node import ResourceNode
from randovania.gui.dialog.scroll_label_dialog import ScrollLabelDialog
from randovania.gui.tracker.tracker_component import TrackerComponent
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach

if typing.TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region import Region
    from randovania.generator.filler.runner import PlayerPool
    from randovania.gui.tracker.tracker_state import TrackerState
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.state import State


class TrackerTextMap(TrackerComponent):
    _last_state: TrackerState
    _region_name_to_item: dict[str, QtWidgets.QTreeWidgetItem]
    _area_name_to_item: dict[tuple[str, str], QtWidgets.QTreeWidgetItem]
    _node_to_item: dict[Node, QtWidgets.QTreeWidgetItem]

    @classmethod
    def create_for(cls, player_pool: PlayerPool, configuration: BaseConfiguration) -> TrackerTextMap:
        logic = Logic(player_pool.game, configuration)
        return cls(logic)

    def __init__(self, logic: Logic):
        super().__init__()
        self.logic = logic
        self.game_description = logic.game

        self.setWindowTitle("Text Map")

        self.root_widget = QtWidgets.QWidget()
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)
        self.setWidget(self.root_widget)

        ###
        # self.root_layout.setSpacing(6)
        # self.root_layout.setContentsMargins(11, 11, 11, 11)
        # self.root_layout.setContentsMargins(4, 4, 4, 4)
        self.resource_filter_check = QtWidgets.QCheckBox(self.root_widget)
        self.resource_filter_check.setObjectName("resource_filter_check")
        self.resource_filter_check.setChecked(True)

        self.root_layout.addWidget(self.resource_filter_check)

        self.hide_collected_resources_check = QtWidgets.QCheckBox(self.root_widget)
        self.hide_collected_resources_check.setObjectName("hide_collected_resources_check")

        self.root_layout.addWidget(self.hide_collected_resources_check)

        self.current_location_label = QtWidgets.QLabel(self.root_widget)
        self.current_location_label.setObjectName("current_location_label")

        self.root_layout.addWidget(self.current_location_label)

        self.possible_locations_tree = QtWidgets.QTreeWidget(self.root_widget)
        self.possible_locations_tree.setObjectName("possible_locations_tree")
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.possible_locations_tree.sizePolicy().hasHeightForWidth())
        self.possible_locations_tree.setSizePolicy(size_policy)
        self.possible_locations_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        self.root_layout.addWidget(self.possible_locations_tree)

        # Text
        _t = QtWidgets.QApplication.translate
        self.resource_filter_check.setText(_t("TrackerWindow", "Show only resources", None))
        self.hide_collected_resources_check.setText(_t("TrackerWindow", "Hide collected resources", None))
        ___qtreewidgetitem = self.possible_locations_tree.headerItem()
        ___qtreewidgetitem.setText(0, _t("TrackerWindow", "Accessible Locations", None))

        # Fields

        self._region_name_to_item = {}
        self._area_name_to_item = {}
        self._node_to_item = {}

        # Create

        self.action_show_path_to_here = QtGui.QAction("Show path to here")
        self.action_show_path_to_here.triggered.connect(self._on_show_path_to_here)
        self.possible_locations_tree.itemDoubleClicked.connect(self._on_tree_node_double_clicked)
        self.possible_locations_tree.insertAction(None, self.action_show_path_to_here)

        # TODO: Dark World names
        for region in self.game_description.region_list.regions:
            region_item = QtWidgets.QTreeWidgetItem(self.possible_locations_tree)
            region_item.setText(0, region.name)
            region_item.setExpanded(True)
            self._region_name_to_item[region.name] = region_item

            for area in region.areas:
                area_item = QtWidgets.QTreeWidgetItem(region_item)
                area_item.area = area
                area_item.setText(0, area.name)
                area_item.setHidden(True)
                self._area_name_to_item[(region.name, area.name)] = area_item

                for node in area.nodes:
                    node_item = QtWidgets.QTreeWidgetItem(area_item)
                    node_item.setText(0, node.name)
                    node_item.node = node
                    if node.is_resource_node:
                        node_item.setFlags(node_item.flags() & ~QtCore.Qt.ItemIsUserCheckable)
                    self._node_to_item[node] = node_item

        # Connect
        self.resource_filter_check.stateChanged.connect(self._refresh_visible_nodes)
        self.hide_collected_resources_check.stateChanged.connect(self._refresh_visible_nodes)

    def _pretty_node_name(self, node: Node) -> str:
        region_list = self.game_description.region_list
        return f"{region_list.area_name(region_list.nodes_to_area(node))} / {node.name}"

    # Text Map things

    @property
    def _show_only_resource_nodes(self) -> bool:
        return self.resource_filter_check.isChecked()

    @property
    def _hide_collected_resources(self) -> bool:
        return self.hide_collected_resources_check.isChecked()

    def _on_show_path_to_here(self):
        target: QtWidgets.QTreeWidgetItem = self.possible_locations_tree.currentItem()
        if target is None:
            return
        node: Node | None = getattr(target, "node", None)
        if node is not None:
            reach = ResolverReach.calculate_reach(self.logic, self._last_state.state)
            try:
                path = reach.path_to_node(node)
            except KeyError:
                path = []

            rl = self.logic.game.region_list
            text = [f"<p><span style='font-weight:600;'>Path to {node.name}</span></p><ul>"]
            for p in path:
                text.append(f"<li>{rl.node_name(p, with_region=True, distinguish_dark_aether=True)}</li>")
            text.append("</ul>")

            dialog = ScrollLabelDialog("".join(text), "Path to node", self)
            dialog.exec_()
        else:
            QtWidgets.QMessageBox.warning(self, "Invalid target",
                                          f"Can't find a path to {target.text(0)}. Please select a node.")

    def _on_tree_node_double_clicked(self, item: QtWidgets.QTreeWidgetItem, _):
        node: Node | None = getattr(item, "node", None)

        # FIXME

        if not item.isDisabled() and node is not None and node != self._last_state.actions[-1]:
            self._add_new_action(node)

    def _refresh_visible_nodes(self):
        context = self._last_state.state.node_context()

        for region in self.game_description.region_list.regions:
            for area in region.areas:
                area_is_visible = False
                for node in area.nodes:
                    is_visible = node in self._last_state.nodes_in_reach

                    node_item = self._node_to_item[node]
                    if node.is_resource_node:
                        resource_node = typing.cast(ResourceNode, node)

                        if self._show_only_resource_nodes:
                            is_visible = is_visible and not isinstance(node, ConfigurableNode)

                        is_collected = resource_node.is_collected(context)
                        is_visible = is_visible and not (self._hide_collected_resources and is_collected)

                        node_item.setDisabled(not resource_node.can_collect(context))
                        node_item.setCheckState(0, QtCore.Qt.Checked if is_collected else QtCore.Qt.Unchecked)

                    elif self._show_only_resource_nodes:
                        is_visible = False

                    node_item.setHidden(not is_visible)
                    area_is_visible = area_is_visible or is_visible
                self._area_name_to_item[(region.name, area.name)].setHidden(not area_is_visible)

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
        self.current_location_label.setText(f"Current location: {self._pretty_node_name(tracker_state.actions[-1])}")
        self._refresh_visible_nodes()

    def focus_on_region(self, region: Region):
        pass

    def focus_on_area(self, area: Area):
        pass
