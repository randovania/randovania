import functools
import json
from pathlib import Path
from typing import Optional, Dict, Set, List, Tuple, Iterator, Union

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMainWindow, QTreeWidgetItem, QCheckBox, QLabel, QGridLayout, QWidget, QMessageBox, \
    QAction

from randovania.game_description import data_reader
from randovania.game_description.game_description import GameDescription
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import Node, ResourceNode, TranslatorGateNode
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import add_resource_gain_to_current_resources
from randovania.generator import base_patches_factory
from randovania.generator.item_pool import pool_creator
from randovania.gui.common_qt_lib import set_default_window_icon
from randovania.gui.custom_spin_box import CustomSpinBox
from randovania.gui.tracker_window_ui import Ui_TrackerWindow
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State, add_pickup_to_state


class InvalidLayoutForTracker(Exception):
    pass


def _load_previous_state(persistence_path: Path,
                         layout_configuration: LayoutConfiguration,
                         ) -> Optional[dict]:
    previous_layout_path = persistence_path.joinpath("layout_configuration.json")
    if not previous_layout_path.is_file():
        return None

    with previous_layout_path.open() as previous_layout_file:
        previous_layout = LayoutConfiguration.from_json_dict(json.load(previous_layout_file))
        if previous_layout != layout_configuration:
            return None

    previous_state_path = persistence_path.joinpath("state.json")
    if not previous_state_path.is_file():
        return None

    with previous_state_path.open() as previous_state_file:
        return json.load(previous_state_file)


class TrackerWindow(QMainWindow, Ui_TrackerWindow):
    # Tracker state
    _collected_pickups: Dict[PickupEntry, int]
    _actions: List[Node]

    # Tracker configuration
    logic: Logic
    game_description: GameDescription
    layout_configuration: LayoutConfiguration
    persistence_path: Path
    _initial_state: State

    # UI tools
    _asset_id_to_item: Dict[int, QTreeWidgetItem]
    _node_to_item: Dict[Node, QTreeWidgetItem]
    _widget_for_pickup: Dict[PickupEntry, Union[QCheckBox, CustomSpinBox]]
    _during_setup = False

    def __init__(self, persistence_path: Path, layout_configuration: LayoutConfiguration):
        super().__init__()
        self.setupUi(self)
        set_default_window_icon(self)

        self.menu_reset_action = QAction("Reset", self)
        self.menu_reset_action.triggered.connect(self._confirm_reset)
        self.menu_bar.addAction(self.menu_reset_action)

        self._collected_pickups = {}
        self._widget_for_pickup = {}
        self._actions = []
        self._asset_id_to_item = {}
        self._node_to_item = {}
        self.layout_configuration = layout_configuration
        self.persistence_path = persistence_path
        self.game_description = data_reader.decode_data(layout_configuration.game_data)

        try:
            base_patches = base_patches_factory.create_base_patches(self.layout_configuration, None,
                                                                    self.game_description)
        except base_patches_factory.MissingRng as e:
            raise InvalidLayoutForTracker("Layout is configured to have random {}, "
                                          "but that isn't supported by the tracker.".format(e))

        pool_patches, item_pool = pool_creator.calculate_item_pool(self.layout_configuration,
                                                                   self.game_description.resource_database,
                                                                   base_patches)

        self.game_description, self._initial_state = logic_bootstrap(layout_configuration,
                                                                     self.game_description,
                                                                     pool_patches)
        self.logic = Logic(self.game_description, layout_configuration)

        self._initial_state.resources["add_self_as_requirement_to_resources"] = 1

        self.resource_filter_check.stateChanged.connect(self.update_locations_tree_for_reachable_nodes)
        self.hide_collected_resources_check.stateChanged.connect(self.update_locations_tree_for_reachable_nodes)
        self.undo_last_action_button.clicked.connect(self._undo_last_action)

        self.configuration_label.setText("Trick Level: {}; Elevators: Vanilla; Starts with:\n{}".format(
            layout_configuration.trick_level_configuration.global_level.value,
            ", ".join(
                resource.short_name
                for resource in pool_patches.starting_items.keys()
            )
        ))

        self.setup_pickups_box(item_pool)
        self.setup_possible_locations_tree()

        self._starting_nodes = {
            node
            for node in self.game_description.world_list.all_nodes
            if node.is_resource_node and node.resource() in self._initial_state.resources
        }

        persistence_path.mkdir(parents=True, exist_ok=True)

        previous_state = _load_previous_state(persistence_path, layout_configuration)
        if previous_state is not None:
            pickup_name_to_pickup = {pickup.name: pickup for pickup in self._collected_pickups.keys()}
            self.bulk_change_quantity({
                pickup_name_to_pickup[pickup_name]: quantity
                for pickup_name, quantity in previous_state["collected_pickups"].items()
            })
            self._add_new_actions([
                self.game_description.world_list.all_nodes[index]
                for index in previous_state["actions"]
            ])
        else:
            with persistence_path.joinpath("layout_configuration.json").open("w") as layout_file:
                json.dump(layout_configuration.as_json, layout_file)
            self._add_new_action(self._initial_state.node)

    def reset(self):
        self.bulk_change_quantity({
            pickup: 0
            for pickup in self._collected_pickups.keys()
        })

        while len(self._actions) > 1:
            self._actions.pop()
            self.actions_list.takeItem(len(self._actions))

        self._refresh_for_new_action()

    def _confirm_reset(self):
        reply = QMessageBox.question(self, "Reset Tracker?", "Do you want to reset the tracker progression?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.reset()

    @property
    def _show_only_resource_nodes(self) -> bool:
        return self.resource_filter_check.isChecked()

    @property
    def _hide_collected_resources(self) -> bool:
        return self.hide_collected_resources_check.isChecked()

    @property
    def _collected_nodes(self) -> Set[ResourceNode]:
        return self._starting_nodes | set(action for action in self._actions if action.is_resource_node)

    def _pretty_node_name(self, node: Node) -> str:
        world_list = self.game_description.world_list
        return "{} / {}".format(world_list.nodes_to_area(node).name, node.name)

    def _refresh_for_new_action(self):
        self.undo_last_action_button.setEnabled(len(self._actions) > 1)
        self.location_box.setTitle("Current location: {}".format(self._pretty_node_name(self._actions[-1])))
        self.update_locations_tree_for_reachable_nodes()

    def _add_new_action(self, node: Node):
        self._add_new_actions([node])

    def _add_new_actions(self, nodes: Iterator[Node]):
        for node in nodes:
            self.actions_list.addItem(self._pretty_node_name(node))
            self._actions.append(node)
        self._refresh_for_new_action()

    def _undo_last_action(self):
        self._actions.pop()
        self.actions_list.takeItem(len(self._actions))
        self._refresh_for_new_action()

    def _on_tree_node_double_clicked(self, item: QTreeWidgetItem, _):
        node: Optional[Node] = getattr(item, "node", None)

        if not item.isDisabled() and node is not None and node != self._actions[-1]:
            self._add_new_action(node)

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
                    is_collected = node in self._collected_nodes
                    is_visible = node in nodes_in_reach and not (self._hide_collected_resources
                                                                 and is_collected)

                    if self._show_only_resource_nodes:
                        is_visible = is_visible and node.is_resource_node

                    node_item = self._node_to_item[node]
                    node_item.setHidden(not is_visible)
                    if node.is_resource_node:
                        resource_node: ResourceNode = node
                        node_item.setDisabled(not resource_node.can_collect(state.patches, state.resources))
                        node_item.setCheckState(0, Qt.Checked if is_collected else Qt.Unchecked)

                    area_is_visible = area_is_visible or is_visible
                self._asset_id_to_item[area.area_asset_id].setHidden(not area_is_visible)

        # Persist the current state
        with self.persistence_path.joinpath("state.json").open("w") as state_file:
            json.dump(
                {
                    "actions": [
                        node.index
                        for node in self._actions
                    ],
                    "collected_pickups": {
                        pickup.name: quantity
                        for pickup, quantity in self._collected_pickups.items()
                    }
                },
                state_file
            )

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
                    if isinstance(node, TranslatorGateNode):
                        translator = self._initial_state.patches.translator_gates[node.gate]
                        node_item.setText(0, "{} ({})".format(node.name, translator.short_name))
                    else:
                        node_item.setText(0, node.name)
                    node_item.node = node
                    if node.is_resource_node:
                        node_item.setFlags(node_item.flags() & ~Qt.ItemIsUserCheckable)
                    self._node_to_item[node] = node_item

    def _change_item_quantity(self, pickup: PickupEntry, use_quantity_as_bool: bool, quantity: int):
        if use_quantity_as_bool:
            if bool(quantity):
                quantity = 1
            else:
                quantity = 0

        self._collected_pickups[pickup] = quantity
        if not self._during_setup:
            self.update_locations_tree_for_reachable_nodes()

    def bulk_change_quantity(self, new_quantity: Dict[PickupEntry, int]):
        self._during_setup = True
        for pickup, quantity in new_quantity.items():
            widget = self._widget_for_pickup[pickup]
            if isinstance(widget, QCheckBox):
                widget.setChecked(quantity > 0)
            else:
                widget.setValue(quantity)
        self._during_setup = False

    def _create_widgets_with_quantity(self,
                                      pickup: PickupEntry,
                                      parent_widget: QWidget,
                                      parent_layout: QGridLayout,
                                      row: int,
                                      quantity: int,
                                      ):
        label = QLabel(parent_widget)
        label.setText(pickup.name)
        parent_layout.addWidget(label, row, 0)

        spin_bix = CustomSpinBox(parent_widget)
        spin_bix.setMaximumWidth(50)
        spin_bix.setMaximum(quantity)
        spin_bix.valueChanged.connect(functools.partial(self._change_item_quantity, pickup, False))
        self._widget_for_pickup[pickup] = spin_bix
        parent_layout.addWidget(spin_bix, row, 1)

    def setup_pickups_box(self, item_pool: List[PickupEntry]):

        parent_widgets: Dict[ItemCategory, Tuple[QWidget, QGridLayout]] = {
            ItemCategory.EXPANSION: (self.expansions_box, self.expansions_layout),
            ItemCategory.ENERGY_TANK: (self.expansions_box, self.expansions_layout),
            ItemCategory.TRANSLATOR: (self.translators_box, self.translators_layout),
            ItemCategory.TEMPLE_KEY: (self.keys_box, self.keys_layout),
            ItemCategory.SKY_TEMPLE_KEY: (self.keys_box, self.keys_layout),
        }
        major_pickup_parent_widgets = (self.upgrades_box, self.upgrades_layout)

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

        pickup_by_name = {}
        pickup_with_quantity = {}

        for pickup in item_pool:
            if pickup.name in pickup_by_name:
                pickup_with_quantity[pickup_by_name[pickup.name]] += 1
            else:
                pickup_by_name[pickup.name] = pickup
                pickup_with_quantity[pickup] = 1

        non_expansions_with_quantity = []

        for pickup, quantity in pickup_with_quantity.items():
            self._collected_pickups[pickup] = 0
            parent_widget, parent_layout = parent_widgets.get(pickup.item_category, major_pickup_parent_widgets)

            row = row_for_parent[parent_widget]

            if parent_widget is self.expansions_box:
                self._create_widgets_with_quantity(pickup, parent_widget, parent_layout, row, quantity)
                row_for_parent[parent_widget] += 1
            else:
                if quantity > 1:
                    non_expansions_with_quantity.append((parent_widget, parent_layout, pickup, quantity))
                else:
                    check_box = QCheckBox(parent_widget)
                    check_box.setText(pickup.name)
                    check_box.stateChanged.connect(functools.partial(self._change_item_quantity, pickup, True))
                    self._widget_for_pickup[pickup] = check_box

                    column = column_for_parent[parent_widget]
                    parent_layout.addWidget(check_box, row, column)
                    column += 1

                    if column >= k_column_count:
                        column = 0
                        row += 1

                    row_for_parent[parent_widget] = row
                    column_for_parent[parent_widget] = column

        for parent_widget, parent_layout, pickup, quantity in non_expansions_with_quantity:
            if column_for_parent[parent_widget] != 0:
                column_for_parent[parent_widget] = 0
                row_for_parent[parent_widget] += 1

            self._create_widgets_with_quantity(pickup, parent_widget, parent_layout,
                                               row_for_parent[parent_widget],
                                               quantity)
            row_for_parent[parent_widget] += 1

    def state_for_current_configuration(self) -> Optional[State]:
        state = self._initial_state.copy()
        state.node = self._actions[-1]

        for pickup, quantity in self._collected_pickups.items():
            for _ in range(quantity):
                add_pickup_to_state(state, pickup)

        for node in self._collected_nodes:
            add_resource_gain_to_current_resources(node.resource_gain_on_collect(state.patches, state.resources),
                                                   state.resources)

        return state
