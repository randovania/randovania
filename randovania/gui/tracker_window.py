import collections
import functools
import json
import math
import typing
from pathlib import Path
from typing import Optional, Dict, Set, List, Tuple, Iterator, Union

from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt

from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements import RequirementAnd, ResourceRequirement, Requirement
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.configurable_node import ConfigurableNode
from randovania.game_description.world.node import Node
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.resource_node import ResourceNode
from randovania.game_description.world.teleporter_node import TeleporterNode
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.layout import translator_configuration
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.generator import generator
from randovania.gui.dialog.scroll_label_dialog import ScrollLabelDialog
from randovania.gui.generated.tracker_window_ui import Ui_TrackerWindow
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.scroll_protected import ScrollProtectedSpinBox
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.lib.teleporters import TeleporterShuffleMode, TeleporterConfiguration
from randovania.layout.preset import Preset
from randovania.layout.versioned_preset import InvalidPreset, VersionedPreset
from randovania.patching.prime import elevators
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State, add_pickup_to_state


class InvalidLayoutForTracker(Exception):
    pass


def _persisted_preset_path(persistence_path: Path) -> Path:
    return persistence_path.joinpath(f"preset.{VersionedPreset.file_extension()}")


def _load_previous_state(persistence_path: Path,
                         game_configuration: BaseConfiguration,
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


class TrackerWindow(QtWidgets.QMainWindow, Ui_TrackerWindow):
    # Tracker state
    _collected_pickups: Dict[PickupEntry, int]
    _actions: List[Node]

    # Tracker configuration
    logic: Logic
    game_description: GameDescription
    game_configuration: BaseConfiguration
    persistence_path: Path
    _initial_state: State
    _elevator_id_to_combo: Dict[NodeIdentifier, QtWidgets.QComboBox]
    _translator_gate_to_combo: Dict[NodeIdentifier, QtWidgets.QComboBox]
    _starting_nodes: Set[ResourceNode]

    # UI tools
    _world_name_to_item: Dict[str, QtWidgets.QTreeWidgetItem]
    _area_name_to_item: Dict[tuple[str, str], QtWidgets.QTreeWidgetItem]
    _node_to_item: Dict[Node, QtWidgets.QTreeWidgetItem]
    _widget_for_pickup: Dict[PickupEntry, Union[QtWidgets.QCheckBox, QtWidgets.QComboBox]]
    _during_setup = False

    @classmethod
    async def create_new(cls, persistence_path: Path, preset: Preset) -> "TrackerWindow":
        result = cls(persistence_path, preset)
        await result.configure()
        return result

    def __init__(self, persistence_path: Path, preset: Preset):
        super().__init__()
        self.setupUi(self)
        set_default_window_icon(self)

        self._collected_pickups = {}
        self._widget_for_pickup = {}
        self._actions = []
        self._world_name_to_item = {}
        self._area_name_to_item = {}
        self._node_to_item = {}
        self.preset = preset
        self.game_configuration = preset.configuration
        self.persistence_path = persistence_path

    async def configure(self):
        player_pool = await generator.create_player_pool(None, self.game_configuration, 0, 1, rng_required=False)
        pool_patches = player_pool.patches

        bootstrap = self.game_configuration.game.generator.bootstrap

        self.game_description, self._initial_state = bootstrap.logic_bootstrap(
            self.preset.configuration,
            player_pool.game,
            pool_patches)
        self.logic = Logic(self.game_description, self.preset.configuration)
        self.map_canvas.select_game(self.game_description.game)

        self._initial_state.resources.add_self_as_requirement_to_resources = True

        self.menu_reset_action.triggered.connect(self._confirm_reset)
        self.resource_filter_check.stateChanged.connect(self.update_locations_tree_for_reachable_nodes)
        self.hide_collected_resources_check.stateChanged.connect(self.update_locations_tree_for_reachable_nodes)
        self.undo_last_action_button.clicked.connect(self._undo_last_action)

        self.configuration_label.setText("Trick Level: {}; Starts with:\n{}".format(
            self.preset.configuration.trick_level.pretty_description,
            ", ".join(
                resource.short_name
                for resource, _ in pool_patches.starting_items.as_resource_gain()
            )
        ))

        self.setup_pickups_box(player_pool.pickups)
        self.setup_possible_locations_tree()
        self.setup_elevators()
        self.setup_translator_gates()

        # Map
        for world in sorted(self.game_description.world_list.worlds, key=lambda x: x.name):
            self.map_world_combo.addItem(world.name, userData=world)

        self.on_map_world_combo(0)
        self.map_world_combo.currentIndexChanged.connect(self.on_map_world_combo)
        self.map_area_combo.currentIndexChanged.connect(self.on_map_area_combo)
        self.map_canvas.set_edit_mode(False)
        self.map_canvas.SelectAreaRequest.connect(self.focus_on_area)

        # Graph Map
        from randovania.gui.widgets.tracker_map import MatplotlibWidget
        self.matplot_widget = MatplotlibWidget(self.tab_graph_map, self.game_description.world_list)
        self.tab_graph_map_layout.addWidget(self.matplot_widget)
        self.map_tab_widget.currentChanged.connect(self._on_tab_changed)

        for world in self.game_description.world_list.worlds:
            self.graph_map_world_combo.addItem(world.name, world)
        self.graph_map_world_combo.currentIndexChanged.connect(self.on_graph_map_world_combo)

        self.persistence_path.mkdir(parents=True, exist_ok=True)
        previous_state = _load_previous_state(self.persistence_path, self.preset.configuration)

        if not self.apply_previous_state(previous_state):
            self.setup_starting_location(None)

            VersionedPreset.with_preset(self.preset).save_to_file(
                _persisted_preset_path(self.persistence_path)
            )
            self._add_new_action(self._initial_state.node)

    def apply_previous_state(self, previous_state: Optional[dict]) -> bool:
        if previous_state is None:
            return False

        starting_location = None
        needs_starting_location = len(self.game_configuration.starting_location.locations) > 1
        configurable_nodes = {}

        try:
            pickup_name_to_pickup = {pickup.name: pickup for pickup in self._collected_pickups.keys()}
            quantity_to_change = {
                pickup_name_to_pickup[pickup_name]: quantity
                for pickup_name, quantity in previous_state["collected_pickups"].items()
            }
            previous_actions = [
                self.game_description.world_list.node_by_identifier(
                    NodeIdentifier.from_string(identifier)
                )
                for identifier in previous_state["actions"]
            ]
            if needs_starting_location:
                starting_location = AreaIdentifier.from_json(previous_state["starting_location"])

            teleporters: Dict[NodeIdentifier, Optional[AreaIdentifier]] = {
                NodeIdentifier.from_json(item["teleporter"]): (
                    AreaIdentifier.from_json(item["data"])
                    if item["data"] is not None else None
                )
                for item in previous_state["elevators"]
            }
            if self.game_configuration.game == RandovaniaGame.METROID_PRIME_ECHOES:
                configurable_nodes = {
                    NodeIdentifier.from_string(identifier): (LayoutTranslatorRequirement(item)
                                                             if item is not None
                                                             else None)
                    for identifier, item in previous_state["configurable_nodes"].items()
                }
        except (KeyError, AttributeError):
            return False

        self.setup_starting_location(starting_location)

        for teleporter, area_location in teleporters.items():
            combo = self._elevator_id_to_combo[teleporter]
            if area_location is None:
                combo.setCurrentIndex(0)
                continue
            for i in range(combo.count()):
                if area_location == combo.itemData(i):
                    combo.setCurrentIndex(i)
                    break

        for identifier, requirement in configurable_nodes.items():
            combo = self._translator_gate_to_combo[identifier]
            for i in range(combo.count()):
                if requirement == combo.itemData(i):
                    combo.setCurrentIndex(i)
                    break

        self.bulk_change_quantity(quantity_to_change)
        self._add_new_actions(previous_actions)

        world_list = self.game_description.world_list
        state = self.state_for_current_configuration()
        self.focus_on_world(world_list.nodes_to_world(state.node))
        self.focus_on_area(world_list.nodes_to_area(state.node))

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
        buttons = QtWidgets.QMessageBox.StandardButton

        reply = QtWidgets.QMessageBox.question(self, "Reset Tracker?", "Do you want to reset the tracker progression?",
                                               buttons.Yes | buttons.No, buttons.No)
        if reply == buttons.Yes:
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

    def _on_tree_node_double_clicked(self, item: QtWidgets.QTreeWidgetItem, _):
        node: Optional[Node] = getattr(item, "node", None)

        if not item.isDisabled() and node is not None and node != self._actions[-1]:
            self._add_new_action(node)

    def _on_show_path_to_here(self):
        target: QtWidgets.QTreeWidgetItem = self.possible_locations_tree.currentItem()
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

    # Map

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

    # Graph Map

    def update_matplot_widget(self, nodes_in_reach: Set[Node]):
        self.matplot_widget.update_for(
            self.graph_map_world_combo.currentData(),
            self.state_for_current_configuration(),
            nodes_in_reach,
        )

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
        context = state.node_context()
        nodes_in_reach = self.current_nodes_in_reach(state)

        if self.map_tab_widget.currentWidget() == self.tab_graph_map:
            self.update_matplot_widget(nodes_in_reach)

        for world in self.game_description.world_list.worlds:
            for area in world.areas:
                area_is_visible = False
                for node in area.nodes:
                    is_visible = node in nodes_in_reach

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
                self._area_name_to_item[(world.name, area.name)].setHidden(not area_is_visible)

        self.map_canvas.set_state(state)
        self.map_canvas.set_visible_nodes({
            node
            for node in nodes_in_reach
            if not self._node_to_item[node].isHidden()
        })

        # Persist the current state
        self.persist_current_state()

    def persist_current_state(self):
        world_list = self.game_description.world_list
        with self.persistence_path.joinpath("state.json").open("w") as state_file:
            json.dump(
                {
                    "actions": [
                        node.identifier.as_string
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
                    "configurable_nodes": {
                        gate.as_string: combo.currentData().value if combo.currentIndex() > 0 else None
                        for gate, combo in self._translator_gate_to_combo.items()
                    },
                    "starting_location": world_list.identifier_for_node(self._initial_state.node
                                                                        ).area_identifier.as_json,
                },
                state_file
            )

    def setup_possible_locations_tree(self):
        """
        Creates the possible_locations_tree with all worlds, areas and nodes.
        """
        self.action_show_path_to_here = QtGui.QAction("Show path to here")
        self.action_show_path_to_here.triggered.connect(self._on_show_path_to_here)
        self.possible_locations_tree.itemDoubleClicked.connect(self._on_tree_node_double_clicked)
        self.possible_locations_tree.insertAction(None, self.action_show_path_to_here)

        # TODO: Dark World names
        for world in self.game_description.world_list.worlds:
            world_item = QtWidgets.QTreeWidgetItem(self.possible_locations_tree)
            world_item.setText(0, world.name)
            world_item.setExpanded(True)
            self._world_name_to_item[world.name] = world_item

            for area in world.areas:
                area_item = QtWidgets.QTreeWidgetItem(world_item)
                area_item.area = area
                area_item.setText(0, area.name)
                area_item.setHidden(True)
                self._area_name_to_item[(world.name, area.name)] = area_item

                for node in area.nodes:
                    node_item = QtWidgets.QTreeWidgetItem(area_item)
                    node_item.setText(0, node.name)
                    node_item.node = node
                    if node.is_resource_node:
                        node_item.setFlags(node_item.flags() & ~Qt.ItemIsUserCheckable)
                    self._node_to_item[node] = node_item

    def setup_elevators(self):
        self._elevator_id_to_combo = {}

        if not hasattr(self.game_configuration, "elevators"):
            return

        elevators_config: TeleporterConfiguration = getattr(self.game_configuration, "elevators")

        world_list = self.game_description.world_list
        nodes_by_world: Dict[str, List[TeleporterNode]] = collections.defaultdict(list)

        areas_to_not_change = {
            "Sky Temple Gateway",
            "Sky Temple Energy Controller",
            "Aerie Transport Station",
            "Aerie",
        }
        targets = {}
        for world, area, node in world_list.all_worlds_areas_nodes:
            if isinstance(node, TeleporterNode) and node.editable and area.name not in areas_to_not_change:
                name = world.correct_name(area.in_dark_aether)
                nodes_by_world[name].append(node)

                location = AreaIdentifier(world.name, area.name)
                targets[elevators.get_short_elevator_or_area_name(self.game_configuration.game, world_list, location,
                                                                  True)] = location

        if elevators_config.mode == TeleporterShuffleMode.ONE_WAY_ANYTHING:
            targets = {}
            for world in world_list.worlds:
                for area in world.areas:
                    name = world.correct_name(area.in_dark_aether)
                    targets[f"{name} - {area.name}"] = AreaIdentifier(world.name, area.name)

        combo_targets = sorted(targets.items(), key=lambda it: it[0])

        for world_name in sorted(nodes_by_world.keys()):
            nodes = nodes_by_world[world_name]
            nodes_locations = [world_list.identifier_for_node(node).area_location
                               for node in nodes]
            nodes_names = [elevators.get_short_elevator_or_area_name(self.game_configuration.game, world_list,
                                                                     location, False)
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
                if elevators_config.is_vanilla:
                    combo.addItem("Vanilla", node.default_connection)
                    combo.setEnabled(False)
                else:
                    combo.addItem("Undefined", None)
                    for target_name, connection in combo_targets:
                        combo.addItem(target_name, connection)

                combo.setMinimumContentsLength(11)
                combo.currentIndexChanged.connect(self.update_locations_tree_for_reachable_nodes)
                self._elevator_id_to_combo[world_list.identifier_for_node(node)] = combo
                layout.addWidget(combo, i, 1)

    def setup_translator_gates(self):
        world_list = self.game_description.world_list
        resource_db = self.game_description.resource_database
        self._translator_gate_to_combo = {}

        if self.game_configuration.game != RandovaniaGame.METROID_PRIME_ECHOES:
            return

        configuration = self.game_configuration
        assert isinstance(configuration, EchoesConfiguration)

        gates = {
            f"{area.name} ({node.name})": world_list.identifier_for_node(node)
            for world, area, node in world_list.all_worlds_areas_nodes
            if isinstance(node, ConfigurableNode)
        }
        translator_requirement = configuration.translator_configuration.translator_requirement

        for i, (gate_name, gate) in enumerate(sorted(gates.items(), key=lambda it: it[0])):
            node_name = QtWidgets.QLabel(self.translator_gate_scroll_contents)
            node_name.setText(gate_name)
            self.translator_gate_scroll_layout.addWidget(node_name, i, 0)

            combo = QtWidgets.QComboBox(self.translator_gate_scroll_contents)
            gate_requirement = translator_requirement[gate]

            if gate_requirement in (LayoutTranslatorRequirement.RANDOM,
                                    LayoutTranslatorRequirement.RANDOM_WITH_REMOVED):
                combo.addItem("Undefined", None)
                for translator in translator_configuration.ITEM_NAMES.keys():
                    combo.addItem(translator.long_name, translator)
            else:
                combo.addItem(gate_requirement.long_name, gate_requirement)
                combo.setEnabled(False)

            combo.currentIndexChanged.connect(self.update_locations_tree_for_reachable_nodes)
            self._translator_gate_to_combo[gate] = combo
            self.translator_gate_scroll_layout.addWidget(combo, i, 1)

    def setup_starting_location(self, area_location: Optional[AreaIdentifier]):
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

        def is_resource_node_present(node: Node, state: State):
            if node.is_resource_node:
                assert isinstance(node, ResourceNode)
                return self._initial_state.resources.is_resource_set(node.resource(state.node_context()))
            return False

        self._starting_nodes = {
            node
            for node in world_list.iterate_nodes()
            if is_resource_node_present(node, self._initial_state)
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
            if isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(quantity > 0)
            else:
                widget.setValue(quantity)
        self._during_setup = False

    def _create_widgets_with_quantity(self,
                                      pickup: PickupEntry,
                                      parent_widget: QtWidgets.QWidget,
                                      parent_layout: QtWidgets.QGridLayout,
                                      row: int,
                                      quantity: int,
                                      ):
        label = QtWidgets.QLabel(parent_widget)
        label.setText(pickup.name)
        parent_layout.addWidget(label, row, 0)

        spin_bix = ScrollProtectedSpinBox(parent_widget)
        spin_bix.setMaximumWidth(50)
        spin_bix.setMaximum(quantity)
        spin_bix.valueChanged.connect(functools.partial(self._change_item_quantity, pickup, False))
        self._widget_for_pickup[pickup] = spin_bix
        parent_layout.addWidget(spin_bix, row, 1)

    def setup_pickups_box(self, item_pool: List[PickupEntry]):

        parent_widgets: Dict[str, Tuple[QtWidgets.QWidget, QtWidgets.QGridLayout]] = {
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
                check_box = QtWidgets.QCheckBox(parent_widget)
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

            # Prepare the rows for the spin boxes below
            row_for_parent[parent_widget] = num_rows
            column_for_parent[parent_widget] = 0

        for parent_widget, parent_layout, pickup, quantity in non_expansions_with_quantity:
            self._create_widgets_with_quantity(pickup, parent_widget, parent_layout,
                                               row_for_parent[parent_widget],
                                               quantity)
            row_for_parent[parent_widget] += 1

        for parent_widget, _ in parent_widgets.values():
            # Nothing was added to this box
            if row_for_parent[parent_widget] == column_for_parent.get(parent_widget) == 0:
                parent_widget.setVisible(False)

    def state_for_current_configuration(self) -> Optional[State]:
        state = self._initial_state.copy()
        if self._actions:
            state.node = self._actions[-1]

        for teleporter, combo in self._elevator_id_to_combo.items():
            state.patches.elevator_connection[teleporter] = combo.currentData()

        for gate, item in self._translator_gate_to_combo.items():
            scan_visor = self.game_description.resource_database.get_item("Scan")

            requirement: Optional[LayoutTranslatorRequirement] = item.currentData()
            if requirement is None:
                translator_req = Requirement.impossible()
            else:
                translator = self.game_description.resource_database.get_item(requirement.item_name)
                translator_req = ResourceRequirement(translator, 1, False)

            state.patches.configurable_nodes[gate] = RequirementAnd([
                ResourceRequirement(scan_visor, 1, False),
                translator_req,
            ])

        for pickup, quantity in self._collected_pickups.items():
            for _ in range(quantity):
                add_pickup_to_state(state, pickup)

        for node in self._collected_nodes:
            state.resources.add_resource_gain(
                node.resource_gain_on_collect(state.node_context())
            )

        return state

    # View
    def focus_on_world(self, world: World):
        self.map_world_combo.setCurrentIndex(self.map_world_combo.findData(world))
        self.graph_map_world_combo.setCurrentIndex(self.graph_map_world_combo.findData(world))
        self.on_map_world_combo(0)

    def focus_on_area(self, area: Area):
        self.map_area_combo.setCurrentIndex(self.map_area_combo.findData(area))
