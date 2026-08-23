from __future__ import annotations

import json
import typing

from PySide6 import QtCore, QtWidgets

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.generator.base_patches_factory import MissingRng
from randovania.generator.pickup_pool import PoolResults, pool_creator
from randovania.gui.generated.tracker_window_ui import Ui_TrackerWindow
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.tracker.tracker_canvas_map import TrackerCanvasMap
from randovania.gui.tracker.tracker_component import TrackerComponent, TrackerComponentSetup
from randovania.gui.tracker.tracker_configurable_nodes import TrackerConfigurableNodes
from randovania.gui.tracker.tracker_pickup_inventory import TrackerPickupInventory
from randovania.gui.tracker.tracker_state import TrackerState
from randovania.gui.tracker.tracker_teleporters import TrackerTeleporters
from randovania.gui.tracker.tracker_text_map import TrackerTextMap
from randovania.layout import filtered_database
from randovania.layout.versioned_preset import InvalidPreset, VersionedPreset
from randovania.lib import json_lib
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach

if typing.TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import NodeIndex
    from randovania.game_description.db.region import Region
    from randovania.game_description.db.resource_node import ResourceNode
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode
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
        previous_configuration: BaseConfiguration = (
            VersionedPreset.from_file_sync(previous_layout_path).get_preset().configuration
        )
    except (FileNotFoundError, json.JSONDecodeError, InvalidPreset):
        return None

    if previous_configuration != game_configuration:
        return None

    previous_state_path = persistence_path.joinpath("state.json")
    try:
        return typing.cast("dict", json_lib.read_path(previous_state_path))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


class TrackerWindow(QtWidgets.QMainWindow, Ui_TrackerWindow):
    """
    Tracks the progress of a playthrough of a given preset.

    This class owns the list of actions taken so far and the resulting State. Everything else is delegated to
    the TrackerComponents docked into it.
    """

    # Tracker state
    _actions: list[WorldGraphNode]

    # Tracker configuration
    logic: Logic
    graph: WorldGraph
    game_description: GameDescription
    game_configuration: BaseConfiguration
    persistence_path: Path
    tracker_components: list[TrackerComponent]
    _initial_state: State
    _starting_nodes_indices: set[NodeIndex]

    # Set while a persisted state is being restored, so half-restored states aren't broadcast to the components.
    _during_setup = False

    # Confirmation to open the tracker
    confirm_open = True

    @classmethod
    async def create_new(cls, persistence_path: Path, preset: Preset) -> TrackerWindow:
        result = cls(persistence_path, preset)

        incompatible = preset.settings_incompatible_with_map_tracker()
        if incompatible:
            description = "Tracker does not support the following features:\n"
            description += "\n".join(incompatible)
            raise InvalidLayoutForTracker(description)

        await result.configure()
        return result

    def __init__(self, persistence_path: Path, preset: Preset) -> None:
        super().__init__()
        self.setupUi(self)
        set_default_window_icon(self)

        self._actions = []
        self.tracker_components = []
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
            game_generator.base_patches_factory.create_static_base_patches(self.game_configuration, game, 0)
            .assign_new_pickups((index, PickupTarget(pickup, 0)) for index, pickup in pool_results.assignment.items())
            .assign_extra_starting_pickups(pool_results.starting)
        )
        patches = self.fill_game_specific(game, patches)

        self.game_description = game
        graph, self._initial_state = game_generator.bootstrap.logic_bootstrap_graph(
            self.preset.configuration, game, patches
        )
        self.graph = graph
        self.logic = Logic(graph, self.preset.configuration, record_paths=True)

        self.menu_reset_action.triggered.connect(self._confirm_reset)
        self.undo_last_action_button.clicked.connect(self._undo_last_action)

        self.configuration_label.setText(
            f"Trick Level: {self.preset.configuration.trick_level.pretty_description(self.game_description)}"
        )

        self.create_components(pool_results)

        self.persistence_path.mkdir(parents=True, exist_ok=True)
        previous_state = _load_previous_state(self.persistence_path, self.preset.configuration)

        if not self.apply_previous_state(previous_state):
            self.setup_starting_location(None)

            # Don't save the tracker if opening the tracker was cancelled
            if not self.confirm_open:
                return

            VersionedPreset.with_preset(self.preset).save_to_file(_persisted_preset_path(self.persistence_path))
            self._add_new_action(self._initial_state.node)

    def create_components(self, pickup_pool: PoolResults) -> None:
        # Imported here as it pulls matplotlib, which is expensive.
        from randovania.gui.tracker.tracker_graph_map import TrackerGraphMap

        setup = TrackerComponentSetup(
            game_description=self.game_description,
            graph=self.graph,
            logic=self.logic,
            configuration=self.game_configuration,
            pickup_pool=pickup_pool,
        )

        first_in_area: dict[QtCore.Qt.DockWidgetArea, TrackerComponent] = {}
        last_in_area: dict[QtCore.Qt.DockWidgetArea, TrackerComponent] = {}

        component_classes: list[type[TrackerComponent]] = [
            TrackerPickupInventory,
            TrackerTeleporters,
            TrackerConfigurableNodes,
            TrackerTextMap,
            TrackerCanvasMap,
            TrackerGraphMap,
        ]

        for component_class in component_classes:
            component = component_class.create_for(setup)
            if component is None:
                continue

            self.tracker_components.append(component)
            self.addDockWidget(component.dock_area, component)

            previous = last_in_area.get(component.dock_area)
            if previous is not None:
                self.tabifyDockWidget(previous, component)
            else:
                first_in_area[component.dock_area] = component
            last_in_area[component.dock_area] = component

            component.StateChanged.connect(self.update_components_for_current_state)
            component.ActionRequested.connect(self._on_action_requested)

        # tabifyDockWidget leaves the last added tab selected, but the first one is the more useful default.
        for component in first_in_area.values():
            component.raise_()

    def apply_previous_state(self, previous_state: dict | None) -> bool:
        if previous_state is None:
            return False

        starting_location = None
        needs_starting_location = len(self.game_configuration.starting_location.locations) > 1

        try:
            previous_actions = [
                self.graph.node_identifier_to_node[NodeIdentifier.from_string(identifier)]
                for identifier in previous_state["actions"]
            ]
            if needs_starting_location:
                starting_location = NodeIdentifier.from_json(previous_state["starting_location"])
        except (KeyError, AttributeError):
            return False

        restored_states = [component.decode_persisted_state(previous_state) for component in self.tracker_components]
        if any(restored is None for restored in restored_states):
            return False

        self.setup_starting_location(starting_location)

        self._during_setup = True
        try:
            for component, restored in zip(self.tracker_components, restored_states, strict=True):
                component.apply_previous_state(restored)
        finally:
            self._during_setup = False

        self._add_new_actions(previous_actions)

        node = self.state_for_current_configuration().node
        self.focus_on_region(node.region)
        self.focus_on_area(node.area)

        return True

    def reset(self) -> None:
        for component in self.tracker_components:
            component.reset()

        while len(self._actions) > 1:
            self._actions.pop()
            self.actions_list.takeItem(len(self._actions))

        self._refresh_for_new_action()

    def _confirm_reset(self) -> None:
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

    # Actions

    @property
    def _collected_nodes(self) -> list[WorldGraphNode]:
        indices = self._starting_nodes_indices | {
            action.node_index for action in self._actions if action.is_resource_node()
        }
        return [self.graph.nodes[index] for index in indices]

    def _pretty_node_name(self, node: WorldGraphNode) -> str:
        return f"{node.identifier.region} - {node.identifier.area} / {node.identifier.node}"

    def _refresh_for_new_action(self) -> None:
        self.undo_last_action_button.setEnabled(len(self._actions) > 1)
        self.update_components_for_current_state()

    def _on_action_requested(self, node: WorldGraphNode) -> None:
        if not self._actions or node != self._actions[-1]:
            self._add_new_action(node)

    def _add_new_action(self, node: WorldGraphNode) -> None:
        self._add_new_actions([node])

    def _add_new_actions(self, nodes: Iterable[WorldGraphNode]) -> None:
        for node in nodes:
            self.actions_list.addItem(self._pretty_node_name(node))
            self._actions.append(node)
        self._refresh_for_new_action()

    def _undo_last_action(self) -> None:
        self._actions.pop()
        self.actions_list.takeItem(len(self._actions))
        self._refresh_for_new_action()

    # State

    def current_nodes_in_reach(self, state: State | None) -> list[WorldGraphNode]:
        nodes_in_reach: list[WorldGraphNode] = []
        if state is not None:
            reach = ResolverReach.calculate_reach(self.logic, state)
            nodes_in_reach = list(reach.nodes)
            if state.node not in nodes_in_reach:
                nodes_in_reach.append(state.node)

        return nodes_in_reach

    def update_components_for_current_state(self) -> None:
        if self._during_setup:
            return

        state = self.state_for_current_configuration()
        tracker_state = TrackerState(
            state,
            self.current_nodes_in_reach(state),
            tuple(self._actions),
        )
        for component in self.tracker_components:
            component.tracker_update(tracker_state)

        # Persist the current state
        self.persist_current_state()

    def state_for_current_configuration(self) -> State:
        for component in self.tracker_components:
            component.update_graph()

        state = self._initial_state.copy()
        if self._actions:
            state.node = self._actions[-1]

        for component in self.tracker_components:
            component.fill_into_state(state)

        for node in self._collected_nodes:
            state.resources.add_resource_gain(node.resource_gain_on_collect(state.resources))

        return state

    def persist_current_state(self) -> None:
        new_state: dict = {
            "actions": [node.identifier.as_string for node in self._actions],
            "starting_location": self._initial_state.node.identifier.as_json,
        }
        for component in self.tracker_components:
            new_state.update(component.persist_current_state())

        json_lib.write_path(self.persistence_path.joinpath("state.json"), new_state)

    def setup_starting_location(self, node_location: NodeIdentifier | None) -> None:
        if node_location is None:
            locations_len = len(self.game_configuration.starting_location.locations)
            if locations_len > 1:
                node_locations = sorted(
                    self.game_configuration.starting_location.locations,
                    key=lambda it: it.display_name(),
                )

                location_names = [it.display_name() for it in node_locations]
                selected_name, self.confirm_open = QtWidgets.QInputDialog.getItem(
                    self, "Starting Location", "Select starting location", location_names, 0, False
                )
                node_location = node_locations[location_names.index(selected_name)]
            elif locations_len == 1:
                node_location = self.game_configuration.starting_location.locations[0]
            else:
                raise ValueError("Preset without a starting location.")

        self._initial_state.node = self.graph.node_identifier_to_node[node_location]

        def is_resource_node_present(node: WorldGraphNode, state: State) -> typing.TypeGuard[ResourceNode]:
            if node.is_resource_node():
                is_resource_set = self._initial_state.resources.is_resource_set
                return all(is_resource_set(resource) for resource, _ in node.resource_gain_on_collect(state.resources))
            return False

        self._starting_nodes_indices = {
            node.node_index for node in self.graph.nodes if is_resource_node_present(node, self._initial_state)
        }

    # View

    def focus_on_region(self, region: Region) -> None:
        for component in self.tracker_components:
            component.focus_on_region(region)

    def focus_on_area(self, area: Area) -> None:
        for component in self.tracker_components:
            component.focus_on_area(area)

    def fill_game_specific(self, game: GameDescription, patches: GamePatches) -> GamePatches:
        try:
            return patches.assign_game_specific(
                game.game.generator.base_patches_factory.create_game_specific(
                    self.game_configuration,
                    game,
                    None,  # type: ignore[arg-type]
                )
            )
        except MissingRng:
            pass

        return game.game.generator.bootstrap.configurable_nodes.get_default_patches(
            self.game_configuration,
            game,
            patches,
        )
