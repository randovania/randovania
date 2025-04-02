from __future__ import annotations

import collections
import functools
import json
import math
import typing

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources import search
from randovania.games.common import elevators
from randovania.games.prime2.layout import translator_configuration
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.generator.base_patches_factory import MissingRng
from randovania.generator.pickup_pool import pool_creator
from randovania.gui.dialog.scroll_label_dialog import ScrollLabelDialog
from randovania.gui.generated.tracker_window_ui import Ui_TrackerWindow
from randovania.gui.lib import signal_handling
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.scroll_protected import ScrollProtectedSpinBox
from randovania.layout import filtered_database
from randovania.layout.lib.teleporters import TeleporterConfiguration, TeleporterShuffleMode
from randovania.layout.versioned_preset import InvalidPreset, VersionedPreset
from randovania.lib import json_lib
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State, add_pickup_to_state

if typing.TYPE_CHECKING:
    from pathlib import Path

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region import Region
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.preset import Preset


class InvalidLayoutForTracker(Exception):
    pass


def _persisted_preset_path(persistence_path: Path) -> Path:
    return persistence_path.joinpath(f"preset.{VersionedPreset.file_extension()}")


def _load_previous_state(
    persistence_path: Path,
    game_configuration: BaseConfiguration,
) -> dict | None:
    previous_layout_path = _persisted_preset_path(persistence_path)
    try:
        previous_configuration = VersionedPreset.from_file_sync(previous_layout_path).get_preset().configuration
    except (FileNotFoundError, json.JSONDecodeError, InvalidPreset):
        return None

    if previous_configuration != game_configuration:
        return None

    previous_state_path = persistence_path.joinpath("state.json")
    try:
        return json_lib.read_path(previous_state_path)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


class TrackerWindow(QtWidgets.QMainWindow, Ui_TrackerWindow):
    # Tracker state
    _collected_pickups: dict[PickupEntry, int]
    _actions: list[Node]

    # Tracker configuration
    logic: Logic
    game_description: GameDescription
    game_configuration: BaseConfiguration
    persistence_path: Path
    _initial_state: State
    _teleporter_id_to_combo: dict[NodeIdentifier, QtWidgets.QComboBox]
    _translator_gate_to_combo: dict[NodeIdentifier, QtWidgets.QComboBox]
    _starting_nodes: set[ResourceNode]

    # UI tools
    _region_name_to_item: dict[str, QtWidgets.QTreeWidgetItem]
    _area_name_to_item: dict[tuple[str, str], QtWidgets.QTreeWidgetItem]
    _node_to_item: dict[Node, QtWidgets.QTreeWidgetItem]
    _widget_for_pickup: dict[PickupEntry, QtWidgets.QCheckBox | ScrollProtectedSpinBox]
    _during_setup = False

    # Confirmation to open the tracker
    confirm_open = True

    @classmethod
    async def create_new(cls, persistence_path: Path, preset: Preset) -> TrackerWindow:
        result = cls(persistence_path, preset)

        if preset.configuration.dock_rando.is_enabled():
            raise InvalidLayoutForTracker("Tracker does not support Door Lock rando")

        if isinstance(preset.configuration, EchoesConfiguration):
            if preset.configuration.portal_rando:
                raise InvalidLayoutForTracker("Tracker does not support Portal rando")

        if preset.game == RandovaniaGame.FACTORIO:
            raise InvalidLayoutForTracker("Tracker does not support Factorio")

        await result.configure()
        return result

    def __init__(self, persistence_path: Path, preset: Preset):
        super().__init__()
        self.setupUi(self)
        set_default_window_icon(self)

        self._collected_pickups = {}
        self._widget_for_pickup = {}
        self._actions = []
        self._region_name_to_item = {}
        self._area_name_to_item = {}
        self._node_to_item = {}
        self.preset = preset
        self.game_configuration = preset.configuration
        self.persistence_path = persistence_path

    async def configure(self) -> None:
        game = filtered_database.game_description_for_layout(self.game_configuration).get_mutable()
        game_generator = game.game.generator
        game.resource_database = game_generator.bootstrap.patch_resource_database(
            game.resource_database,
            self.game_configuration,
        )

        pool_results = pool_creator.calculate_pool_results(self.game_configuration, game)
        patches = (
            game.game.generator.base_patches_factory.create_static_base_patches(self.game_configuration, game, 0)
            .assign_new_pickups((index, PickupTarget(pickup, 0)) for index, pickup in pool_results.assignment.items())
            .assign_extra_starting_pickups(pool_results.starting)
        )
        bootstrap = self.game_configuration.game.generator.bootstrap

        patches = self.fill_game_specific(game, patches)

        self.game_description, self._initial_state = bootstrap.logic_bootstrap(
            self.preset.configuration,
            game,
            patches,
        )
        self.logic = Logic(self.game_description, self.preset.configuration)
        self.map_canvas.select_game(self.game_description.game)

        self._initial_state.resources.add_self_as_requirement_to_resources = True

        self.menu_reset_action.triggered.connect(self._confirm_reset)
        self.resource_filter_check.stateChanged.connect(self.update_locations_tree_for_reachable_nodes)
        self.hide_collected_resources_check.stateChanged.connect(self.update_locations_tree_for_reachable_nodes)
        self.undo_last_action_button.clicked.connect(self._undo_last_action)

        self.configuration_label.setText(
            "Trick Level: {}; Starts with:\n{}".format(
                self.preset.configuration.trick_level.pretty_description(self.game_description),
                ", ".join(resource.short_name for resource, _ in patches.starting_resources().as_resource_gain()),
            )
        )

        self.setup_pickups_box(pool_results.to_place)
        self.setup_possible_locations_tree()
        self.setup_teleporters()
        self.setup_translator_gates()

        # Map
        for region in sorted(self.game_description.region_list.regions, key=lambda x: x.name):
            self.map_region_combo.addItem(region.name, userData=region)

        self.on_map_region_combo(0)
        self.map_region_combo.currentIndexChanged.connect(self.on_map_region_combo)
        self.map_area_combo.currentIndexChanged.connect(self.on_map_area_combo)
        self.map_canvas.set_edit_mode(False)
        self.map_canvas.SelectAreaRequest.connect(self.focus_on_area)
        self.map_canvas.SelectNodeRequest.connect(self._add_new_action)

        # Graph Map
        from randovania.gui.widgets.tracker_map import MatplotlibWidget

        self.matplot_widget = MatplotlibWidget(self.tab_graph_map, self.game_description.region_list)
        self.tab_graph_map_layout.addWidget(self.matplot_widget)
        self.map_tab_widget.currentChanged.connect(self._on_tab_changed)

        for region in self.game_description.region_list.regions:
            self.graph_map_region_combo.addItem(region.name, region)
        self.graph_map_region_combo.currentIndexChanged.connect(self.on_graph_map_region_combo)

        self.persistence_path.mkdir(parents=True, exist_ok=True)
        previous_state = _load_previous_state(self.persistence_path, self.preset.configuration)

        if not self.apply_previous_state(previous_state):
            self.setup_starting_location(None)

            # Don't save the tracker if opening the tracker was cancelled
            if not self.confirm_open:
                return

            VersionedPreset.with_preset(self.preset).save_to_file(_persisted_preset_path(self.persistence_path))
            self._add_new_action(self._initial_state.node)

    def apply_previous_state(self, previous_state: dict | None) -> bool:
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
                self.game_description.region_list.node_by_identifier(NodeIdentifier.from_string(identifier))
                for identifier in previous_state["actions"]
            ]
            if needs_starting_location:
                starting_location = NodeIdentifier.from_json(previous_state["starting_location"])

            teleporters: dict[NodeIdentifier, NodeIdentifier | None] = {
                NodeIdentifier.from_json(item["teleporter"]): (
                    NodeIdentifier.from_json(item["data"]) if item["data"] is not None else None
                )
                for item in previous_state["teleporters"]
            }
            if self.game_configuration.game == RandovaniaGame.METROID_PRIME_ECHOES:
                configurable_nodes = {
                    NodeIdentifier.from_string(identifier): (
                        LayoutTranslatorRequirement(item) if item is not None else None
                    )
                    for identifier, item in previous_state["configurable_nodes"].items()
                }
        except (KeyError, AttributeError):
            return False

        self.setup_starting_location(starting_location)

        for teleporter, node_location in teleporters.items():
            combo = self._teleporter_id_to_combo[teleporter]
            if node_location is None:
                combo.setCurrentIndex(0)
                continue
            for i in range(combo.count()):
                if node_location == combo.itemData(i):
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

        region_list = self.game_description.region_list
        state = self.state_for_current_configuration()
        self.focus_on_region(region_list.nodes_to_region(state.node))
        self.focus_on_area(region_list.nodes_to_area(state.node))

        return True

    def reset(self):
        self.bulk_change_quantity(dict.fromkeys(self._collected_pickups.keys(), 0))

        while len(self._actions) > 1:
            self._actions.pop()
            self.actions_list.takeItem(len(self._actions))

        for teleporter in self._teleporter_id_to_combo.values():
            teleporter.setCurrentIndex(0)
        for teleporter in self._translator_gate_to_combo.values():
            teleporter.setCurrentIndex(0)

        self._refresh_for_new_action()

    def _confirm_reset(self):
        buttons = QtWidgets.QMessageBox.StandardButton

        reply = QtWidgets.QMessageBox.question(
            self,
            "Reset Tracker?",
            "Do you want to reset the tracker progression?",
            buttons.Yes | buttons.No,
            buttons.No,
        )
        if reply == buttons.Yes:
            self.reset()

    @property
    def _show_only_resource_nodes(self) -> bool:
        return self.resource_filter_check.isChecked()

    @property
    def _hide_collected_resources(self) -> bool:
        return self.hide_collected_resources_check.isChecked()

    @property
    def _collected_nodes(self) -> set[ResourceNode]:
        return self._starting_nodes | {action for action in self._actions if action.is_resource_node}

    def _pretty_node_name(self, node: Node) -> str:
        region_list = self.game_description.region_list
        return f"{region_list.area_name(region_list.nodes_to_area(node))} / {node.name}"

    def _refresh_for_new_action(self):
        self.undo_last_action_button.setEnabled(len(self._actions) > 1)
        self.current_location_label.setText(f"Current location: {self._pretty_node_name(self._actions[-1])}")
        self.update_locations_tree_for_reachable_nodes()

    def _add_new_action(self, node: Node):
        self._add_new_actions([node])

    def _add_new_actions(self, nodes: typing.Iterable[Node]):
        for node in nodes:
            self.actions_list.addItem(self._pretty_node_name(node))
            self._actions.append(node)
        self._refresh_for_new_action()

    def _undo_last_action(self):
        self._actions.pop()
        self.actions_list.takeItem(len(self._actions))
        self._refresh_for_new_action()

    def _on_tree_node_double_clicked(self, item: QtWidgets.QTreeWidgetItem, _):
        node: Node | None = getattr(item, "node", None)

        if not item.isDisabled() and node is not None and node != self._actions[-1]:
            self._add_new_action(node)

    def _on_show_path_to_here(self):
        target: QtWidgets.QTreeWidgetItem = self.possible_locations_tree.currentItem()
        if target is None:
            return
        node: Node | None = getattr(target, "node", None)
        if node is not None:
            reach = ResolverReach.calculate_reach(self.logic, self.state_for_current_configuration())
            try:
                path = reach.path_to_node(node)
            except KeyError:
                path = []

            wl = self.logic.game.region_list
            text = [f"<p><span style='font-weight:600;'>Path to {node.name}</span></p><ul>"]
            for p in path:
                text.append(f"<li>{wl.node_name(p, with_region=True, distinguish_dark_aether=True)}</li>")
            text.append("</ul>")

            dialog = ScrollLabelDialog(self, "".join(text), "Path to node")
            dialog.exec_()
        else:
            QtWidgets.QMessageBox.warning(
                self, "Invalid target", f"Can't find a path to {target.text(0)}. Please select a node."
            )

    # Map

    def on_map_region_combo(self, _):
        region: Region = self.map_region_combo.currentData()
        self.map_area_combo.clear()
        for area in sorted(region.areas, key=lambda x: x.name):
            self.map_area_combo.addItem(area.name, userData=area)

        self.map_canvas.select_region(region)
        self.on_map_area_combo(0)

    def on_map_area_combo(self, _):
        area: Area = self.map_area_combo.currentData()
        self.map_canvas.select_area(area)

    # Graph Map

    def update_matplot_widget(self, nodes_in_reach: set[Node]):
        self.matplot_widget.update_for(
            self.graph_map_region_combo.currentData(),
            self.state_for_current_configuration(),
            nodes_in_reach,
        )

    def on_graph_map_region_combo(self):
        nodes_in_reach = self.current_nodes_in_reach(self.state_for_current_configuration())
        self.update_matplot_widget(nodes_in_reach)

    def current_nodes_in_reach(self, state: State | None):
        if state is None:
            nodes_in_reach = set()
        else:
            reach = ResolverReach.calculate_reach(self.logic, state)
            nodes_in_reach = set(reach.nodes)
            nodes_in_reach.add(state.node)
        return nodes_in_reach

    def _on_tab_changed(self):
        if self.map_tab_widget.currentWidget() == self.tab_graph_map:
            self.on_graph_map_region_combo()

    def update_locations_tree_for_reachable_nodes(self):
        self.update_translator_gates()

        state = self.state_for_current_configuration()
        context = state.node_context()
        nodes_in_reach = self.current_nodes_in_reach(state)

        if self.map_tab_widget.currentWidget() == self.tab_graph_map:
            self.update_matplot_widget(nodes_in_reach)

        for region in self.game_description.region_list.regions:
            for area in region.areas:
                area_is_visible = False
                for node in area.nodes:
                    is_visible = node in nodes_in_reach

                    node_item = self._node_to_item[node]
                    if node.is_resource_node:
                        resource_node = typing.cast("ResourceNode", node)

                        if self._show_only_resource_nodes:
                            is_visible = is_visible and not isinstance(node, ConfigurableNode)

                        is_collected = resource_node.is_collected(context)
                        is_visible = is_visible and not (self._hide_collected_resources and is_collected)

                        node_item.setDisabled(
                            not (
                                resource_node.should_collect(context)
                                and resource_node.requirement_to_collect().satisfied(
                                    context, state.health_for_damage_requirements
                                )
                            )
                        )
                        node_item.setCheckState(
                            0, QtCore.Qt.CheckState.Checked if is_collected else QtCore.Qt.CheckState.Unchecked
                        )

                    elif self._show_only_resource_nodes:
                        is_visible = False

                    node_item.setHidden(not is_visible)
                    area_is_visible = area_is_visible or is_visible
                self._area_name_to_item[(region.name, area.name)].setHidden(not area_is_visible)

        self.map_canvas.set_state(state)
        self.map_canvas.set_visible_nodes(nodes_in_reach)

        # Persist the current state
        self.persist_current_state()

    def persist_current_state(self):
        json_lib.write_path(
            self.persistence_path.joinpath("state.json"),
            {
                "actions": [node.identifier.as_string for node in self._actions],
                "collected_pickups": {pickup.name: quantity for pickup, quantity in self._collected_pickups.items()},
                "teleporters": [
                    {
                        "teleporter": teleporter.as_json,
                        "data": combo.currentData().as_json if combo.currentIndex() > 0 else None,
                    }
                    for teleporter, combo in self._teleporter_id_to_combo.items()
                ],
                "configurable_nodes": {
                    gate.as_string: combo.currentData().value if combo.currentIndex() > 0 else None
                    for gate, combo in self._translator_gate_to_combo.items()
                },
                "starting_location": self._initial_state.node.identifier.as_json,
            },
        )

    def setup_possible_locations_tree(self):
        """
        Creates the possible_locations_tree with all regions, areas and nodes.
        """
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
                        node_item.setFlags(node_item.flags() & ~Qt.ItemIsUserCheckable)
                    self._node_to_item[node] = node_item

    def setup_teleporters(self) -> None:
        self._teleporter_id_to_combo = {}

        if not hasattr(self.game_configuration, "teleporters"):
            return

        teleporters_config: TeleporterConfiguration = getattr(self.game_configuration, "teleporters")

        region_list = self.game_description.region_list
        nodes_by_region: dict[str, list[DockNode]] = collections.defaultdict(list)

        targets = {}
        teleporter_dock_types = self.game_description.dock_weakness_database.all_teleporter_dock_types
        for region, area, node in region_list.all_regions_areas_nodes:
            if isinstance(node, DockNode) and node.dock_type in teleporter_dock_types:
                name = region.correct_name(area.in_dark_aether)
                nodes_by_region[name].append(node)

                location = node.identifier
                targets[elevators.get_elevator_or_area_name(self.game_description, region_list, location, True)] = (
                    location
                )

        if teleporters_config.mode == TeleporterShuffleMode.ONE_WAY_ANYTHING:
            targets = {}
            for region in region_list.regions:
                for area in region.areas:
                    if area.has_start_node():
                        name = region.correct_name(area.in_dark_aether)
                        targets[f"{name} - {area.name}"] = area.get_start_nodes()[0].identifier

        combo_targets = sorted(targets.items(), key=lambda it: it[0])

        for region_name in sorted(nodes_by_region.keys()):
            nodes = nodes_by_region[region_name]
            nodes_locations = [node.identifier for node in nodes]
            nodes_names = [
                elevators.get_elevator_or_area_name(self.game_description, region_list, location, False)
                for location in nodes_locations
            ]

            group = QtWidgets.QGroupBox(self.teleporters_scroll_contents)
            group.setTitle(region_name)
            self.teleporters_scroll_layout.addWidget(group)
            layout = QtWidgets.QGridLayout(group)

            for i, (node, location, name) in enumerate(
                sorted(zip(nodes, nodes_locations, nodes_names), key=lambda it: it[2])
            ):
                node_name = QtWidgets.QLabel(group)
                node_name.setText(name)
                node_name.setWordWrap(True)
                node_name.setMinimumWidth(75)
                layout.addWidget(node_name, i, 0)

                combo = QtWidgets.QComboBox(group)
                if teleporters_config.is_vanilla:
                    combo.addItem("Vanilla", node.default_connection)
                    combo.setEnabled(False)
                else:
                    combo.addItem("Undefined", None)
                    for target_name, connection in combo_targets:
                        combo.addItem(target_name, connection)

                combo.setMinimumContentsLength(11)
                combo.currentIndexChanged.connect(self.update_locations_tree_for_reachable_nodes)
                self._teleporter_id_to_combo[node.identifier] = combo
                layout.addWidget(combo, i, 1)

    def update_translator_gates(self) -> None:
        # It'd be nice to use EchoesBoostrap.apply_game_specific_patches
        # But we need to support a magical "Impossible" kind of gate, in case there's no selection

        game = self.game_description
        if game.game != RandovaniaGame.METROID_PRIME_ECHOES:
            return

        scan_visor = search.find_resource_info_with_long_name(game.resource_database.item, "Scan Visor")
        scan_visor_req = ResourceRequirement.simple(scan_visor)

        for node in game.region_list.iterate_nodes_of_type(ConfigurableNode):
            combo = self._translator_gate_to_combo[node.identifier]
            requirement: LayoutTranslatorRequirement | None = combo.currentData()

            if requirement is None:
                translator_req = Requirement.impossible()
            else:
                translator = game.resource_database.get_item(requirement.item_name)
                translator_req = ResourceRequirement.simple(translator)

            game.region_list.configurable_nodes[node.identifier] = RequirementAnd(
                [scan_visor_req, translator_req],
            )

    def setup_translator_gates(self):
        region_list = self.game_description.region_list
        self._translator_gate_to_combo = {}

        if self.game_configuration.game != RandovaniaGame.METROID_PRIME_ECHOES:
            return

        configuration = self.game_configuration
        assert isinstance(configuration, EchoesConfiguration)

        gates = {
            f"{area.name} ({node.name})": node.identifier
            for region, area, node in region_list.all_regions_areas_nodes
            if isinstance(node, ConfigurableNode)
        }
        translator_requirement = configuration.translator_configuration.translator_requirement

        for i, (gate_name, gate) in enumerate(sorted(gates.items(), key=lambda it: it[0])):
            node_name = QtWidgets.QLabel(self.translator_gate_scroll_contents)
            node_name.setText(gate_name)
            self.translator_gate_scroll_layout.addWidget(node_name, i, 0)

            combo = QtWidgets.QComboBox(self.translator_gate_scroll_contents)
            gate_requirement = translator_requirement[gate]

            if gate_requirement in (
                LayoutTranslatorRequirement.RANDOM,
                LayoutTranslatorRequirement.RANDOM_WITH_REMOVED,
            ):
                combo.addItem("Undefined", None)
                for translator in translator_configuration.ITEM_NAMES.keys():
                    combo.addItem(translator.long_name, translator)
            else:
                combo.addItem(gate_requirement.long_name, gate_requirement)
                combo.setEnabled(False)

            combo.currentIndexChanged.connect(self.update_locations_tree_for_reachable_nodes)
            self._translator_gate_to_combo[gate] = combo
            self.translator_gate_scroll_layout.addWidget(combo, i, 1)

    def setup_starting_location(self, node_location: NodeIdentifier | None) -> None:
        region_list = self.game_description.region_list

        if node_location is None:
            locations_len = len(self.game_configuration.starting_location.locations)
            if locations_len > 1:
                node_locations = sorted(
                    self.game_configuration.starting_location.locations,
                    key=lambda it: region_list.node_name(region_list.node_by_identifier(it), with_region=True),
                )

                location_names = [
                    region_list.node_name(region_list.node_by_identifier(it), with_region=True) for it in node_locations
                ]
                selected_name, self.confirm_open = QtWidgets.QInputDialog.getItem(
                    self, "Starting Location", "Select starting location", location_names, 0, False
                )
                node_location = node_locations[location_names.index(selected_name)]
            elif locations_len == 1:
                node_location = self.game_configuration.starting_location.locations[0]
            else:
                raise ValueError("Preset without a starting location.")

        node = region_list.node_by_identifier(node_location)
        self._initial_state.node = node

        def is_resource_node_present(node: Node, state: State) -> typing.TypeGuard[ResourceNode]:
            if node.is_resource_node:
                assert isinstance(node, ResourceNode)
                is_resource_set = self._initial_state.resources.is_resource_set
                return all(
                    is_resource_set(resource) for resource, _ in node.resource_gain_on_collect(state.node_context())
                )
            return False

        self._starting_nodes = {
            node for node in region_list.iterate_nodes() if is_resource_node_present(node, self._initial_state)
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

    def bulk_change_quantity(self, new_quantity: dict[PickupEntry, int]):
        self._during_setup = True
        for pickup, quantity in new_quantity.items():
            widget = self._widget_for_pickup[pickup]
            if isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(quantity > 0)
            else:
                widget.setValue(quantity)
        self._during_setup = False

    def _create_widgets_with_quantity(
        self,
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

    def setup_pickups_box(self, item_pool: list[PickupEntry]):
        parent_widgets: dict[str, tuple[QtWidgets.QWidget, QtWidgets.QGridLayout]] = {
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
        pickup_with_quantity: dict[PickupEntry, int] = {}

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
            parent_widget, parent_layout = parent_widgets.get(pickup.gui_category.name, major_pickup_parent_widgets)

            row = row_for_parent[parent_widget]

            if parent_widget is self.expansions_box:
                self._create_widgets_with_quantity(pickup, parent_widget, parent_layout, row, quantity)
                row_for_parent[parent_widget] += 1
            else:
                if quantity > 1:
                    non_expansions_with_quantity.append((parent_widget, parent_layout, pickup, quantity))
                else:
                    without_quantity_by_parent[parent_widget].append((parent_layout, pickup))

        for parent_widget, layouts in without_quantity_by_parent.items():
            num_rows = math.ceil(len(layouts) / k_column_count)
            for parent_layout, pickup in layouts:
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
            self._create_widgets_with_quantity(
                pickup, parent_widget, parent_layout, row_for_parent[parent_widget], quantity
            )
            row_for_parent[parent_widget] += 1

        for parent_widget, _ in parent_widgets.values():
            # Nothing was added to this box
            if row_for_parent[parent_widget] == column_for_parent.get(parent_widget) == 0:
                parent_widget.setVisible(False)

    def state_for_current_configuration(self) -> State | None:
        state = self._initial_state.copy()
        if self._actions:
            state.node = self._actions[-1]

        region_list = self.game_description.region_list

        state.patches = state.patches.assign_dock_connections(
            (
                region_list.typed_node_by_identifier(teleporter, DockNode),
                # TODO If there is no `default_node` anymore, what would be the replacement?
                region_list.node_by_identifier(combo.currentData()),
            )
            for teleporter, combo in self._teleporter_id_to_combo.items()
            if combo.currentData() is not None
        )

        for pickup, quantity in self._collected_pickups.items():
            for _ in range(quantity):
                add_pickup_to_state(state, pickup)

        for node in self._collected_nodes:
            state.resources.add_resource_gain(node.resource_gain_on_collect(state.node_context()))

        return state

    # View
    def focus_on_region(self, region: Region):
        signal_handling.set_combo_with_value(self.map_region_combo, region)
        signal_handling.set_combo_with_value(self.graph_map_region_combo, region)
        self.on_map_region_combo(0)

    def focus_on_area(self, area: Area):
        signal_handling.set_combo_with_value(self.map_area_combo, area)

    def fill_game_specific(self, game: GameDescription, patches: GamePatches) -> GamePatches:
        try:
            return patches.assign_game_specific(
                game.game.generator.base_patches_factory.create_game_specific(
                    self.game_configuration,
                    game,
                    None,
                )
            )
        except MissingRng:
            pass

        if game.game != RandovaniaGame.METROID_PRIME_ECHOES:
            raise NotImplementedError

        return patches.assign_game_specific(
            {
                "translator_gates": {
                    node.identifier.as_string: LayoutTranslatorRequirement.VIOLET
                    for node in game.region_list.iterate_nodes_of_type(ConfigurableNode)
                }
            }
        )
