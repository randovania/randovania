import collections
import functools
import json
import math
import typing
import logging
from pathlib import Path
from random import Random
from typing import Optional, Dict, Set, List, Tuple, Iterator, Union

import matplotlib.pyplot as plt
import networkx
from PySide2 import QtWidgets
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMainWindow, QTreeWidgetItem, QCheckBox, QLabel, QGridLayout, QWidget, QMessageBox
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements import RequirementAnd
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import add_resource_gain_to_current_resources
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.world.dock import DockLockType
from randovania.game_description.world.node import Node, ResourceNode, TranslatorGateNode, TeleporterNode, DockNode
from randovania.game_description.world.teleporter import Teleporter
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame
from randovania.games.prime import elevators
from randovania.generator import generator
from randovania.gui.dialog.scroll_label_dialog import ScrollLabelDialog
from randovania.gui.generated.tracker_window_ui import Ui_TrackerWindow
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.scroll_protected import ScrollProtectedSpinBox
from randovania.layout.game_to_class import AnyGameConfiguration
from randovania.layout.lib.teleporters import TeleporterShuffleMode
from randovania.layout.preset import Preset
from randovania.layout.preset_migration import VersionedPreset, InvalidPreset
from randovania.layout.prime2 import translator_configuration
from randovania.layout.prime2.echoes_configuration import EchoesConfiguration
from randovania.layout.prime2.translator_configuration import LayoutTranslatorRequirement
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State, add_pickup_to_state


class InvalidLayoutForTracker(Exception):
    pass


def _persisted_preset_path(persistence_path: Path) -> Path:
    return persistence_path.joinpath(f"preset.{VersionedPreset.file_extension()}")


def _load_previous_state(persistence_path: Path,
                         game_configuration: AnyGameConfiguration,
                         ) -> Optional[dict]:
    previous_layout_path = _persisted_preset_path(persistence_path)
    try:
        previous_configuration = VersionedPreset.from_file_sync(previous_layout_path).get_preset().configuration
    except (FileNotFoundError, json.JSONDecodeError, InvalidPreset):
        return None

    if previous_configuration != game_configuration:
        return None

    previous_state_path = persistence_path.joinpath("state.json")
    try:
        with previous_state_path.open() as previous_state_file:
            return json.load(previous_state_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


class MatplotlibWidget(QtWidgets.QWidget):
    ax: Axes

    def __init__(self, parent=None):
        super().__init__(parent)

        fig = Figure(figsize=(7, 5), dpi=65, facecolor=(1, 1, 1), edgecolor=(0, 0, 0))
        self.canvas = FigureCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.toolbar)
        lay.addWidget(self.canvas)

        self.ax = fig.add_subplot(111)
        self.line, *_ = self.ax.plot([])


class TrackerWindow(QMainWindow, Ui_TrackerWindow):
    # Tracker state
    _collected_pickups: Dict[PickupEntry, int]
    _actions: List[Node]

    # Tracker configuration
    logic: Logic
    game_description: GameDescription
    game_configuration: EchoesConfiguration
    persistence_path: Path
    _initial_state: State
    _elevator_id_to_combo: Dict[Teleporter, QtWidgets.QComboBox]
    _translator_gate_to_combo: Dict[TranslatorGate, QtWidgets.QComboBox]
    _starting_nodes: Set[ResourceNode]
    _undefined_item = ItemResourceInfo(-1, "Undefined", "Undefined", 0, None)

    # UI tools
    _asset_id_to_item: Dict[int, QTreeWidgetItem]
    _node_to_item: Dict[Node, QTreeWidgetItem]
    _widget_for_pickup: Dict[PickupEntry, Union[QCheckBox, QtWidgets.QComboBox]]
    _during_setup = False

    def __init__(self, persistence_path: Path, preset: Preset):
        super().__init__()
        self.setupUi(self)
        set_default_window_icon(self)

        self._collected_pickups = {}
        self._widget_for_pickup = {}
        self._actions = []
        self._asset_id_to_item = {}
        self._node_to_item = {}
        self.game_configuration = preset.configuration
        self.persistence_path = persistence_path

        player_pool = generator.create_player_pool(Random(0), self.game_configuration, 0, 1)
        pool_patches = player_pool.patches
        self.game_description, self._initial_state = logic_bootstrap(preset.configuration,
                                                                     player_pool.game,
                                                                     pool_patches)
        self.logic = Logic(self.game_description, preset.configuration)

        self._initial_state.resources["add_self_as_requirement_to_resources"] = 1

        self.menu_reset_action.triggered.connect(self._confirm_reset)
        self.resource_filter_check.stateChanged.connect(self.update_locations_tree_for_reachable_nodes)
        self.hide_collected_resources_check.stateChanged.connect(self.update_locations_tree_for_reachable_nodes)
        self.undo_last_action_button.clicked.connect(self._undo_last_action)

        self.configuration_label.setText("Trick Level: {}; Starts with:\n{}".format(
            preset.configuration.trick_level.pretty_description,
            ", ".join(
                resource.short_name
                for resource in pool_patches.starting_items.keys()
            )
        ))

        self.setup_pickups_box(player_pool.pickups)
        self.setup_possible_locations_tree()
        self.setup_elevators()
        self.setup_translator_gates()

        self.matplot_widget = MatplotlibWidget(self.tab_graph_map)
        self.tab_graph_map_layout.addWidget(self.matplot_widget)
        self._world_to_node_positions = {}
        self.map_tab_widget.currentChanged.connect(self._on_tab_changed)

        for world in self.game_description.world_list.worlds:
            self.graph_map_world_combo.addItem(world.name, world)
        self.graph_map_world_combo.currentIndexChanged.connect(self.on_graph_map_world_combo)

        persistence_path.mkdir(parents=True, exist_ok=True)
        previous_state = _load_previous_state(persistence_path, preset.configuration)

        if not self.apply_previous_state(previous_state):
            self.setup_starting_location(None)

            VersionedPreset.with_preset(preset).save_to_file(
                _persisted_preset_path(persistence_path)
            )
            self._add_new_action(self._initial_state.node)

    def apply_previous_state(self, previous_state: Optional[dict]) -> bool:
        if previous_state is None:
            return False

        starting_location = None
        needs_starting_location = len(self.game_configuration.starting_location.locations) > 1
        resource_db = self.game_description.resource_database
        translator_gates = {}

        try:
            pickup_name_to_pickup = {pickup.name: pickup for pickup in self._collected_pickups.keys()}
            quantity_to_change = {
                pickup_name_to_pickup[pickup_name]: quantity
                for pickup_name, quantity in previous_state["collected_pickups"].items()
            }
            previous_actions = [
                self.game_description.world_list.all_nodes[index]
                for index in previous_state["actions"]
            ]
            if needs_starting_location:
                starting_location = AreaLocation.from_json(previous_state["starting_location"])

            elevators: Dict[Teleporter, Optional[AreaLocation]] = {
                Teleporter.from_json(item["teleporter"]): (
                    AreaLocation.from_json(item["data"])
                    if item["data"] is not None else None
                )
                for item in previous_state["elevators"]
            }
            if self.game_configuration.game == RandovaniaGame.METROID_PRIME_ECHOES:
                translator_gates = {
                    TranslatorGate(int(gate)): (resource_db.get_item(item)
                                                if item is not None
                                                else self._undefined_item)
                    for gate, item in previous_state["translator_gates"].items()
                }
        except KeyError:
            return False

        self.setup_starting_location(starting_location)

        for teleporter, area_location in elevators.items():
            combo = self._elevator_id_to_combo[teleporter]
            if area_location is None:
                combo.setCurrentIndex(0)
                continue
            for i in range(combo.count()):
                if area_location == combo.itemData(i):
                    combo.setCurrentIndex(i)
                    break

        for gate, item in translator_gates.items():
            combo = self._translator_gate_to_combo[gate]
            for i in range(combo.count()):
                if item == combo.itemData(i):
                    combo.setCurrentIndex(i)
                    break

        self.bulk_change_quantity(quantity_to_change)
        self._add_new_actions(previous_actions)
        return True

    def reset(self):
        self.bulk_change_quantity({
            pickup: 0
            for pickup in self._collected_pickups.keys()
        })

        while len(self._actions) > 1:
            self._actions.pop()
            self.actions_list.takeItem(len(self._actions))

        for elevator in self._elevator_id_to_combo.values():
            elevator.setCurrentIndex(0)
        for elevator in self._translator_gate_to_combo.values():
            elevator.setCurrentIndex(0)

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
        return "{} / {}".format(world_list.area_name(world_list.nodes_to_area(node)), node.name)

    def _refresh_for_new_action(self):
        self.undo_last_action_button.setEnabled(len(self._actions) > 1)
        self.current_location_label.setText("Current location: {}".format(self._pretty_node_name(self._actions[-1])))
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

    def _on_show_path_to_here(self):
        target: QTreeWidgetItem = self.possible_locations_tree.currentItem()
        if target is None:
            return
        node: Optional[Node] = getattr(target, "node", None)
        if node is not None:
            reach = ResolverReach.calculate_reach(self.logic, self.state_for_current_configuration())
            path = reach.path_to_node.get(node, [])

            wl = self.logic.game.world_list
            text = [f"<p><span style='font-weight:600;'>Path to {node.name}</span></p><ul>"]
            for p in path:
                text.append("<li>{}</li>".format(wl.node_name(p, with_world=True, distinguish_dark_aether=True)))
            text.append("</ul>")

            dialog = ScrollLabelDialog("".join(text), "Path to node", self)
            dialog.exec_()
        else:
            QtWidgets.QMessageBox.warning(self, "Invalid target",
                                          "Can't find a path to {}. Please select a node.".format(target.text(0)))

    def _positions_for_world(self, world: World):
        g = networkx.DiGraph()
        world_list = self.game_description.world_list
        state = self.state_for_current_configuration()

        for area in world.areas:
            g.add_node(area)

        for area in world.areas:
            nearby_areas = set()
            for node in area.nodes:
                if isinstance(node, DockNode):
                    try:
                        target_node = world_list.resolve_dock_node(node, state.patches)
                        if target_node is not None:
                            nearby_areas.add(world_list.nodes_to_area(target_node))
                    except IndexError as e:
                        logging.error(f"For {node.name} in {area.name}, received {e}")
                        continue
            for other_area in nearby_areas:
                g.add_edge(area, other_area)

        return networkx.drawing.spring_layout(g)

    def update_matplot_widget(self, nodes_in_reach: Set[Node]):
        g = networkx.DiGraph()
        world_list = self.game_description.world_list
        state = self.state_for_current_configuration()

        world: World = self.graph_map_world_combo.currentData()
        for area in world.areas:
            g.add_node(area)

        for area in world.areas:
            nearby_areas = set()
            for node in area.nodes:
                if node not in nodes_in_reach:
                    continue

                if isinstance(node, DockNode):
                    try:
                        target_node = world_list.resolve_dock_node(node, state.patches)
                        if target_node is None:
                            continue
                        forward_weakness = state.patches.dock_weakness.get((area.area_asset_id, node.dock_index),
                                                                           node.default_dock_weakness)
                        requirement = forward_weakness.requirement
                        # TODO: only add requirement if the blast shield has not been destroyed yet

                        if isinstance(target_node, DockNode):
                            # TODO: Target node is expected to be a dock. Should this error?
                            back_weakness = state.patches.dock_weakness.get(
                                (world_list.nodes_to_area(target_node).area_asset_id, target_node.dock_index),
                                target_node.default_dock_weakness)
                            if back_weakness.lock_type == DockLockType.FRONT_BLAST_BACK_BLAST:
                                requirement = RequirementAnd([requirement, back_weakness.requirement])

                        if requirement.satisfied(state.resources, state.energy, state.resource_database):
                            nearby_areas.add(world_list.nodes_to_area(target_node))

                    except IndexError as e:
                        logging.error(f"For {node.name} in {area.name}, received {e}")
                        continue

            for other_area in nearby_areas:
                g.add_edge(area, other_area)

        self.matplot_widget.ax.clear()

        cf = self.matplot_widget.ax.get_figure()
        cf.set_facecolor("w")

        if world.world_asset_id not in self._world_to_node_positions:
            self._world_to_node_positions[world.world_asset_id] = self._positions_for_world(world)
        pos = self._world_to_node_positions[world.world_asset_id]

        networkx.draw_networkx_nodes(g, pos, ax=self.matplot_widget.ax)
        networkx.draw_networkx_edges(g, pos, arrows=True, ax=self.matplot_widget.ax)
        networkx.draw_networkx_labels(g, pos, ax=self.matplot_widget.ax,
                                      labels={area: area.name for area in world.areas},
                                      verticalalignment='top')

        self.matplot_widget.ax.set_axis_off()

        plt.draw_if_interactive()
        self.matplot_widget.canvas.draw()

    def on_graph_map_world_combo(self):
        nodes_in_reach = self.current_nodes_in_reach(self.state_for_current_configuration())
        self.update_matplot_widget(nodes_in_reach)

    def current_nodes_in_reach(self, state: Optional[State]):
        if state is None:
            nodes_in_reach = set()
        else:
            reach = ResolverReach.calculate_reach(self.logic, state)
            nodes_in_reach = set(reach.nodes)
            nodes_in_reach.add(state.node)
        return nodes_in_reach

    def _on_tab_changed(self):
        if self.map_tab_widget.currentWidget() == self.tab_graph_map:
            self.on_graph_map_world_combo()

    def update_locations_tree_for_reachable_nodes(self):
        state = self.state_for_current_configuration()
        nodes_in_reach = self.current_nodes_in_reach(state)
        if self.map_tab_widget.currentWidget() == self.tab_graph_map:
            self.update_matplot_widget(nodes_in_reach)

        all_nodes = self.game_description.world_list.all_nodes
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
                        resource_node = typing.cast(ResourceNode, node)
                        node_item.setDisabled(not resource_node.can_collect(state.patches, state.resources, all_nodes,
                                                                            state.resource_database))
                        node_item.setCheckState(0, Qt.Checked if is_collected else Qt.Unchecked)

                    area_is_visible = area_is_visible or is_visible
                self._asset_id_to_item[area.area_asset_id].setHidden(not area_is_visible)

        # Persist the current state
        self.persist_current_state()

    def persist_current_state(self):
        world_list = self.game_description.world_list
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
                    },
                    "elevators": [
                        {
                            "teleporter": teleporter.as_json,
                            "data": combo.currentData().as_json if combo.currentIndex() > 0 else None
                        }
                        for teleporter, combo in self._elevator_id_to_combo.items()
                    ],
                    "translator_gates": {
                        str(gate.index): combo.currentData().index if combo.currentIndex() > 0 else None
                        for gate, combo in self._translator_gate_to_combo.items()
                    },
                    "starting_location": world_list.node_to_area_location(self._initial_state.node).as_json,
                },
                state_file
            )

    def setup_possible_locations_tree(self):
        """
        Creates the possible_locations_tree with all worlds, areas and nodes.
        """
        self.action_show_path_to_here = QtWidgets.QAction("Show path to here")
        self.action_show_path_to_here.triggered.connect(self._on_show_path_to_here)
        self.possible_locations_tree.itemDoubleClicked.connect(self._on_tree_node_double_clicked)
        self.possible_locations_tree.insertAction(None, self.action_show_path_to_here)

        # TODO: Dark World names
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
                        node_item.setText(0, "{} ({})".format(node.name, node.gate))
                    else:
                        node_item.setText(0, node.name)
                    node_item.node = node
                    if node.is_resource_node:
                        node_item.setFlags(node_item.flags() & ~Qt.ItemIsUserCheckable)
                    self._node_to_item[node] = node_item

    def setup_elevators(self):
        world_list = self.game_description.world_list
        nodes_by_world: Dict[str, List[TeleporterNode]] = collections.defaultdict(list)
        self._elevator_id_to_combo = {}

        areas_to_not_change = {
            2278776548,  # Sky Temple Gateway
            2068511343,  # Sky Temple Energy Controller
            3136899603,  # Aerie Transport Station
            1564082177,  # Aerie
        }
        targets = {}
        for world, area, node in world_list.all_worlds_areas_nodes:
            if isinstance(node, TeleporterNode) and node.editable and area.area_asset_id not in areas_to_not_change:
                name = world.correct_name(area.in_dark_aether)
                nodes_by_world[name].append(node)

                location = AreaLocation(world.world_asset_id, area.area_asset_id)
                targets[elevators.get_short_elevator_or_area_name(self.game_configuration.game, world_list, location, True)] = location

        if self.game_configuration.elevators.mode == TeleporterShuffleMode.ONE_WAY_ANYTHING:
            targets = {}
            for world in world_list.worlds:
                for area in world.areas:
                    name = world.correct_name(area.in_dark_aether)
                    targets[f"{name} - {area.name}"] = AreaLocation(world.world_asset_id, area.area_asset_id)

        combo_targets = sorted(targets.items(), key=lambda it: it[0])

        for world_name in sorted(nodes_by_world.keys()):
            nodes = nodes_by_world[world_name]
            nodes_locations = [AreaLocation(world_list.nodes_to_world(node).world_asset_id,
                                            world_list.nodes_to_area(node).area_asset_id)
                               for node in nodes]
            nodes_names = [elevators.get_short_elevator_or_area_name(self.game_configuration.game, world_list, location, False)
                           for location in nodes_locations]

            group = QtWidgets.QGroupBox(self.elevators_scroll_contents)
            group.setTitle(world_name)
            self.elevators_scroll_layout.addWidget(group)
            layout = QtWidgets.QGridLayout(group)

            for i, (node, location, name) in enumerate(sorted(zip(nodes, nodes_locations, nodes_names),
                                                              key=lambda it: it[2])):
                node_name = QtWidgets.QLabel(group)
                node_name.setText(name)
                node_name.setWordWrap(True)
                node_name.setMinimumWidth(75)
                layout.addWidget(node_name, i, 0)

                combo = QtWidgets.QComboBox(group)
                if self.game_configuration.elevators.is_vanilla:
                    combo.addItem("Vanilla", node.default_connection)
                    combo.setEnabled(False)
                else:
                    combo.addItem("Undefined", None)
                    for target_name, connection in combo_targets:
                        combo.addItem(target_name, connection)

                combo.setMinimumContentsLength(11)
                combo.currentIndexChanged.connect(self.update_locations_tree_for_reachable_nodes)
                self._elevator_id_to_combo[node.teleporter] = combo
                layout.addWidget(combo, i, 1)

    def setup_translator_gates(self):
        world_list = self.game_description.world_list
        resource_db = self.game_description.resource_database
        self._translator_gate_to_combo = {}

        if self.game_configuration.game != RandovaniaGame.METROID_PRIME_ECHOES:
            return

        gates = {
            f"{area.name} ({node.gate.index})": node.gate
            for world, area, node in world_list.all_worlds_areas_nodes
            if isinstance(node, TranslatorGateNode)
        }
        translator_requirement = self.game_configuration.translator_configuration.translator_requirement

        for i, (gate_name, gate) in enumerate(sorted(gates.items(), key=lambda it: it[0])):
            node_name = QtWidgets.QLabel(self.translator_gate_scroll_contents)
            node_name.setText(gate_name)
            self.translator_gate_scroll_layout.addWidget(node_name, i, 0)

            combo = QtWidgets.QComboBox(self.translator_gate_scroll_contents)
            gate_requirement = translator_requirement[gate]

            if gate_requirement in (LayoutTranslatorRequirement.RANDOM,
                                    LayoutTranslatorRequirement.RANDOM_WITH_REMOVED):
                combo.addItem("Undefined", self._undefined_item)
                for translator, index in translator_configuration.ITEM_INDICES.items():
                    combo.addItem(translator.long_name, resource_db.get_item(index))
            else:
                combo.addItem(gate_requirement.long_name, resource_db.get_item(gate_requirement.item_index))
                combo.setEnabled(False)

            combo.currentIndexChanged.connect(self.update_locations_tree_for_reachable_nodes)
            self._translator_gate_to_combo[gate] = combo
            self.translator_gate_scroll_layout.addWidget(combo, i, 1)

    def setup_starting_location(self, area_location: Optional[AreaLocation]):
        world_list = self.game_description.world_list

        if len(self.game_configuration.starting_location.locations) > 1:
            if area_location is None:
                area_locations = sorted(self.game_configuration.starting_location.locations,
                                        key=lambda it: world_list.area_name(world_list.area_by_area_location(it)))

                location_names = [world_list.area_name(world_list.area_by_area_location(it))
                                  for it in area_locations]
                selected_name = QtWidgets.QInputDialog.getItem(self, "Starting Location", "Select starting location",
                                                               location_names, 0, False)
                area_location = area_locations[location_names.index(selected_name[0])]

            self._initial_state.node = world_list.resolve_teleporter_connection(area_location)

        self._starting_nodes = {
            node
            for node in world_list.all_nodes
            if node.is_resource_node and node.resource() in self._initial_state.resources
        }

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

        spin_bix = ScrollProtectedSpinBox(parent_widget)
        spin_bix.setMaximumWidth(50)
        spin_bix.setMaximum(quantity)
        spin_bix.valueChanged.connect(functools.partial(self._change_item_quantity, pickup, False))
        self._widget_for_pickup[pickup] = spin_bix
        parent_layout.addWidget(spin_bix, row, 1)

    def setup_pickups_box(self, item_pool: List[PickupEntry]):

        parent_widgets: Dict[str, Tuple[QWidget, QGridLayout]] = {
            "expansion": (self.expansions_box, self.expansions_layout),
            "energy_tank": (self.expansions_box, self.expansions_layout),
            "translator": (self.translators_box, self.translators_layout),
            "temple_key": (self.keys_box, self.keys_layout),
            "sky_temple_key": (self.keys_box, self.keys_layout),
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
        without_quantity_by_parent = collections.defaultdict(list)

        for pickup, quantity in pickup_with_quantity.items():
            self._collected_pickups[pickup] = 0
            parent_widget, parent_layout = parent_widgets.get(pickup.item_category.name, major_pickup_parent_widgets)

            row = row_for_parent[parent_widget]

            if parent_widget is self.expansions_box:
                self._create_widgets_with_quantity(pickup, parent_widget, parent_layout, row, quantity)
                row_for_parent[parent_widget] += 1
            else:
                if quantity > 1:
                    non_expansions_with_quantity.append((parent_widget, parent_layout, pickup, quantity))
                else:
                    without_quantity_by_parent[parent_widget].append((parent_layout, pickup))

        for parent_widget, l in without_quantity_by_parent.items():
            num_rows = math.ceil(len(l) / k_column_count)
            for parent_layout, pickup in l:
                check_box = QCheckBox(parent_widget)
                check_box.setText(pickup.name)
                check_box.stateChanged.connect(functools.partial(self._change_item_quantity, pickup, True))
                self._widget_for_pickup[pickup] = check_box

                row = row_for_parent[parent_widget]
                column = column_for_parent[parent_widget]
                parent_layout.addWidget(check_box, row, column)
                row += 1

                if row >= num_rows:
                    row = 0
                    column += 1

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
        all_nodes = self.game_description.world_list.all_nodes

        state = self._initial_state.copy()
        if self._actions:
            state.node = self._actions[-1]

        for teleporter, combo in self._elevator_id_to_combo.items():
            state.patches.elevator_connection[teleporter] = combo.currentData()

        for gate, item in self._translator_gate_to_combo.items():
            state.patches.translator_gates[gate] = item.currentData()

        for pickup, quantity in self._collected_pickups.items():
            for _ in range(quantity):
                add_pickup_to_state(state, pickup)

        for node in self._collected_nodes:
            add_resource_gain_to_current_resources(node.resource_gain_on_collect(state.patches, state.resources,
                                                                                 all_nodes, state.resource_database),
                                                   state.resources)

        return state
