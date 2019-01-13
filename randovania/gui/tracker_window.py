import functools
from typing import Optional, Dict, Set

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMainWindow, QTreeWidgetItem, QCheckBox, QLabel, QGridLayout

from randovania.game_description import data_reader
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import Node
from randovania.game_description.resources import PickupEntry
from randovania.gui.common_qt_lib import set_default_window_icon
from randovania.gui.custom_spin_box import CustomSpinBox
from randovania.gui.tracker_window_ui import Ui_TrackerWindow
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.layout_configuration import LayoutConfiguration
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State, add_resource_gain_to_state


class TrackerWindow(QMainWindow, Ui_TrackerWindow):
    # Tracker state
    _selected_node: Node
    _collected_pickups: Dict[PickupEntry, int] = {}
    _collected_nodes: Set[Node]

    # Tracker configuration
    logic: Logic
    game_description: GameDescription
    layout_configuration: LayoutConfiguration
    _initial_state: State

    # UI tools
    _asset_id_to_item: Dict[int, QTreeWidgetItem] = {}
    _node_to_item: Dict[Node, QTreeWidgetItem] = {}

    def __init__(self, layout_configuration: LayoutConfiguration):
        super().__init__()
        self.setupUi(self)
        set_default_window_icon(self)

        self.layout_configuration = layout_configuration
        self.game_description = data_reader.decode_data(layout_configuration.game_data, True)

        self.logic, self._initial_state = logic_bootstrap(layout_configuration,
                                                          self.game_description, GamePatches.empty())
        self._update_selected_node(self._initial_state.node)
        self._collected_nodes = {
            node
            for node in self.game_description.world_list.all_nodes
            if node.is_resource_node and node.resource() in self._initial_state.resources
        }
        self.resource_filter_check.stateChanged.connect(self.update_locations_tree_for_reachable_nodes)
        self.hide_collected_resources_check.stateChanged.connect(self.update_locations_tree_for_reachable_nodes)

        self.configuration_label.setText("Trick Level: {}; Elevators: Vanilla; Item Loss: {}".format(
            layout_configuration.trick_level.value,
            layout_configuration.item_loss.value,
        ))

        self.setup_pickups_box()
        self.setup_possible_locations_tree()
        self.update_locations_tree_for_reachable_nodes()

    @property
    def _show_only_resource_nodes(self) -> bool:
        return self.resource_filter_check.isChecked()

    @property
    def _hide_collected_resources(self) -> bool:
        return self.hide_collected_resources_check.isChecked()

    def _update_selected_node(self, node: Node):
        self._selected_node = node

        world_list = self.game_description.world_list
        self.location_box.setTitle("Current location: {} / {}".format(world_list.nodes_to_area(node).name, node.name))

    def _on_tree_node_double_clicked(self, item: QTreeWidgetItem, _):
        node: Optional[Node] = getattr(item, "node", None)

        if node is not None:
            if node.is_resource_node:
                self._collected_nodes.add(node)
                item.setCheckState(0, Qt.Checked)
            self._update_selected_node(node)
            self.update_locations_tree_for_reachable_nodes()

    def update_locations_tree_for_reachable_nodes(self):
        # Calculate which nodes are in reach right now
        state = self.state_for_current_configuration()
        if state is None:
            nodes_in_reach = set()
        else:
            reach = ResolverReach.calculate_reach(self.logic, state)
            nodes_in_reach = set(reach.nodes)
            nodes_in_reach.add(state.node)

        for world in self.game_description.world_list.worlds:
            for area in world.areas:
                area_is_visible = False
                for node in area.nodes:
                    is_visible = node in nodes_in_reach
                    if self._show_only_resource_nodes:
                        is_visible = is_visible and node.is_resource_node
                        if self._hide_collected_resources and node in self._collected_nodes:
                            is_visible = False

                    self._node_to_item[node].setHidden(not is_visible)
                    area_is_visible = area_is_visible or is_visible
                self._asset_id_to_item[area.area_asset_id].setHidden(not area_is_visible)

    def setup_possible_locations_tree(self):
        """
        Creates the possible_locations_tree with all worlds, areas and nodes.
        """
        self.possible_locations_tree.itemDoubleClicked.connect(self._on_tree_node_double_clicked)

        for world in self.game_description.world_list.worlds:
            world_item = QTreeWidgetItem(self.possible_locations_tree)
            world_item.setText(0, world.name)
            world_item.setExpanded(True)
            self._asset_id_to_item[world.world_asset_id] = world_item

            for area in world.areas:
                area_item = QTreeWidgetItem(world_item)
                area_item.area = area
                area_item.setText(0, area.name)
                area_item.setHidden(True)
                self._asset_id_to_item[area.area_asset_id] = area_item

                for node in area.nodes:
                    node_item = QTreeWidgetItem(area_item)
                    node_item.setText(0, node.name)
                    node_item.node = node
                    if node.is_resource_node:
                        node_item.setFlags(node_item.flags() & ~Qt.ItemIsUserCheckable)
                        node_item.setCheckState(0, Qt.Checked if node in self._collected_nodes else Qt.Unchecked)

                    self._node_to_item[node] = node_item

    def _change_item_quantity(self, pickup: PickupEntry, use_quantity_as_bool: bool, quantity: int):
        if use_quantity_as_bool:
            if bool(quantity):
                quantity = 1
            else:
                quantity = 0

        self._collected_pickups[pickup] = quantity
        self.update_locations_tree_for_reachable_nodes()

    def setup_pickups_box(self):
        pickup_database = self.game_description.pickup_database

        parent_widgets = {
            "expansion": (self.expansions_box, self.expansions_layout),
            "energy_tank": (self.expansions_box, self.expansions_layout),
            "translator": (self.translators_box, self.translators_layout),
            "major": (self.upgrades_box, self.upgrades_layout),
            "temple_key": (self.keys_box, self.keys_layout),
            "sky_temple_key": (self.keys_box, self.keys_layout),
        }

        row_for_parent = {
            self.expansions_box: 0,
            self.translators_box: 0,
            self.upgrades_box: 0,
            self.keys_box: 0,
        }
        column_for_parent = {
            self.translators_box: 0,
            self.upgrades_box: 0,
            self.keys_box: 0,
        }
        k_column_count = 2

        for pickup in pickup_database.pickups.values():
            quantity = pickup_database.original_quantity_for(pickup)

            self._collected_pickups[pickup] = 0

            parent_layout: QGridLayout
            parent_widget, parent_layout = parent_widgets[pickup.item_category]

            row = row_for_parent[parent_widget]

            if parent_widget is self.expansions_box:
                if quantity < 2:
                    continue

                label = QLabel(parent_widget)
                label.setText(pickup.name)
                parent_layout.addWidget(label, row, 0)

                spin_bix = CustomSpinBox(parent_widget)
                spin_bix.setMaximumWidth(50)
                spin_bix.setMaximum(quantity)
                spin_bix.valueChanged.connect(functools.partial(self._change_item_quantity, pickup, False))
                parent_layout.addWidget(spin_bix, row, 1)

                row_for_parent[parent_widget] += 1
            else:
                check_box = QCheckBox(parent_widget)
                check_box.setText(pickup.name)
                check_box.stateChanged.connect(functools.partial(self._change_item_quantity, pickup, True))

                column = column_for_parent[parent_widget]
                parent_layout.addWidget(check_box, row, column)
                column += 1

                if column >= k_column_count:
                    column = 0
                    row += 1

                row_for_parent[parent_widget] = row
                column_for_parent[parent_widget] = column

    def state_for_current_configuration(self) -> Optional[State]:
        state = self._initial_state.copy()
        state.node = self._selected_node

        for pickup, quantity in self._collected_pickups.items():
            for _ in range(quantity):
                add_resource_gain_to_state(state, pickup.resource_gain())

        for node in self._collected_nodes:
            add_resource_gain_to_state(state, node.resource_gain_on_collect(state.patches))

        return state
