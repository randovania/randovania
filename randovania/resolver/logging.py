from __future__ import annotations

import abc
import typing
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Literal, NamedTuple, Protocol, final

from randovania.game_description.db.dock_lock_node import DockLockNode
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.event_pickup import EventPickupNode
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.resources.resource_type import ResourceType
from randovania.graph.world_graph import WorldGraphNode
from randovania.resolver import debug

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from randovania.game_description.assignment import PickupTarget
    from randovania.game_description.db.node import NodeIndex
    from randovania.game_description.requirements.requirement_set import RequirementSet
    from randovania.game_description.resources.node_resource_info import NodeResourceInfo
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_info import ResourceGainTuple
    from randovania.graph.state import GraphOrClassicNode, State
    from randovania.resolver.damage_state import DamageState
    from randovania.resolver.logic import Logic
    from randovania.resolver.resolver import ActionPriority


class ActionType(str, Enum):
    MAJOR_PICKUP = "Major"
    MINOR_PICKUP = "Minor"
    EVENT = "Event"
    LOCK = "Lock"
    HINT = "Hint"
    OTHER = "Other"


class ActionDetails(Protocol):
    @property
    def action_type(self) -> ActionType: ...

    @property
    def text(self) -> str: ...


def _get_pickup_action_details(state: State, pickup_index: PickupIndex) -> PickupActionDetails:
    target = state.patches.pickup_assignment.get(pickup_index, None)
    if target is not None and target.pickup.show_in_credits_spoiler:
        action_type = ActionType.MAJOR_PICKUP
    else:
        action_type = ActionType.MINOR_PICKUP
    return PickupActionDetails(action_type, target)


def action_details_from_state(state: State, node: GraphOrClassicNode | None = None) -> ActionDetails | None:
    node = node or state.node

    if isinstance(node, WorldGraphNode):
        if node.pickup_index is not None:
            return _get_pickup_action_details(state, node.pickup_index)
        node = node.database_node
    else:
        if isinstance(node, EventPickupNode):
            node = node.pickup_node

        if isinstance(node, PickupNode):
            return _get_pickup_action_details(state, node.pickup_index)

    text = node.name

    if isinstance(node, EventNode):
        action_type = ActionType.EVENT
    elif isinstance(node, DockNode | DockLockNode):
        action_type = ActionType.LOCK
    elif isinstance(node, HintNode):
        action_type = ActionType.HINT
        if not text.startswith("Hint - "):
            text = f"Hint - {text}"
    elif not node.is_resource_node:
        return None
    else:
        action_type = ActionType.OTHER

    return GenericActionDetails(action_type, text)


class GenericActionDetails(NamedTuple):
    action_type: ActionType
    text: str


class PickupActionDetails(NamedTuple):
    action_type: ActionType
    target: PickupTarget | None

    @property
    def text(self) -> str:
        if self.target is None:
            return f"{ActionType.MINOR_PICKUP.value} - Nothing"
        return f"{self.action_type.value} - {self.target}"


class ActionLogEntry(NamedTuple):
    location: GraphOrClassicNode
    state_string: str
    details: ActionDetails | None
    resources: ResourceGainTuple
    path_from_previous: tuple[GraphOrClassicNode, ...]

    @property
    def simple_state(self) -> str:
        # FIXME: this is not very resilient against changes
        # to State.game_state_debug_string()
        return self.state_string.removesuffix(" Energy")

    def resource_string(self, *, full_types: bool = False) -> str:
        resources: list[str] = []
        for resource, quantity in sorted(self.resources, key=lambda gain: gain[0].resource_type):
            type_name = resource.resource_type.name
            resource_name = resource.long_name

            if not full_types:
                type_name = type_name[0]
            else:
                if resource.resource_type == ResourceType.NODE_IDENTIFIER:
                    # "Node_identifier" is a bit too verbose
                    # for something that's user-facing
                    type_name = "Node"
                    resource_name = typing.cast("NodeResourceInfo", resource).node_identifier.node
                else:
                    type_name = type_name.capitalize()

            text = f"{type_name}: {resource_name}"

            if quantity > 1:
                text += f" x{quantity}"

            resources.append(text)

        return ", ".join(resources)


class RollbackLogEntry(NamedTuple):
    location: GraphOrClassicNode
    details: ActionDetails | None
    has_action: bool
    possible_action: bool
    additional_requirements: RequirementSet


class SkipLogEntry(NamedTuple):
    location: GraphOrClassicNode
    details: ActionDetails
    additional_requirements: RequirementSet


LogFeature = Literal[
    "Action",
    "ActionPath",
    "ActionEnergy",
    "Rollback",
    "RollbackAdditional",
    "Skip",
    "CheckSatisfiable",
    "Completion",
]


class ResolverLogger(abc.ABC):
    last_printed_additional: dict[NodeIndex, RequirementSet]

    def logger_start(self) -> None:
        """Initialize the logger for a new resolver run."""
        self.last_printed_additional = {}

    def node_string(self, node: GraphOrClassicNode, with_region: bool = True) -> str:
        """Standard display format for nodes."""
        return node.full_name(with_region=with_region) if node is not None else "None"

    @property
    def log_levels_used(self) -> Iterator[debug.LogLevel]:
        yield from self._visible_features.keys()

    @cached_property
    def _visible_features(self) -> Mapping[debug.LogLevel, frozenset[LogFeature]]:
        """Which features should be displayed at each log level"""
        visibility: dict[debug.LogLevel, frozenset[LogFeature]] = {}

        visibility[debug.LogLevel.SILENT] = frozenset()

        visibility[debug.LogLevel.NORMAL] = visibility[debug.LogLevel.SILENT] | {
            "Action",
            "Rollback",
            "Completion",
        }

        visibility[debug.LogLevel.HIGH] = visibility[debug.LogLevel.NORMAL] | {
            "ActionEnergy",
            "RollbackAdditional",
            "Skip",
            "CheckSatisfiable",
        }

        visibility[debug.LogLevel.EXTREME] = visibility[debug.LogLevel.HIGH] | {
            "ActionPath",
        }

        return visibility

    def should_show(self, feature: LogFeature, log_level: debug.LogLevel) -> bool:
        """Should this log feature be displayed at this log level?"""
        return feature in self._visible_features[log_level]

    @property
    def should_perform_logging(self) -> bool:
        """
        If False, skips creating LogEntry objects, improving performance
        in circumstances where they're not necessary.
        """
        return True

    @final
    def log_action(self, state: State) -> None:
        """Logs an action performed by the resolver."""
        if not self.should_perform_logging:
            return

        resources: ResourceGainTuple = ()
        if isinstance(state.node, ResourceNode | WorldGraphNode):
            context_state = state.previous_state or state
            resources = tuple(state.node.resource_gain_on_collect(context_state.node_context()))

        self._log_action(
            ActionLogEntry(
                state.node,
                state.game_state_debug_string(),
                action_details_from_state(state),
                resources,
                state.path_from_previous_state,
            )
        )

    @abc.abstractmethod
    def _log_action(self, action_entry: ActionLogEntry) -> None:
        """Internal logic for logging actions."""

    @final
    def log_checking_satisfiable(
        self, actions: Iterable[tuple[ActionPriority, ResourceNode | WorldGraphNode, DamageState]]
    ) -> None:
        """Logs a list of satisfiable actions at this stage in the resolver process."""
        if not self.should_perform_logging:
            return
        self._log_checking_satisfiable(actions)

    @abc.abstractmethod
    def _log_checking_satisfiable(
        self, actions: Iterable[tuple[ActionPriority, ResourceNode | WorldGraphNode, DamageState]]
    ) -> None:
        """Internal logic for logging checking satisifiable actions."""

    @final
    def log_rollback(self, state: State, has_action: bool, possible_action: bool, logic: Logic) -> None:
        """Logs an action being rolled back by the resolver."""
        if not self.should_perform_logging:
            return
        self._log_rollback(
            RollbackLogEntry(
                state.node,
                action_details_from_state(state),
                has_action,
                possible_action,
                logic.get_additional_requirements(state.node),
            )
        )

    @abc.abstractmethod
    def _log_rollback(self, rollback_entry: RollbackLogEntry) -> None:
        """Internal logic for logging rollbacks."""

    @final
    def log_skip(self, node: GraphOrClassicNode, state: State, logic: Logic) -> None:
        """
        Logs an action being skipped by the resolver
        because of missing requirements.
        """
        if not self.should_perform_logging:
            return
        details = action_details_from_state(state, node)
        assert details is not None
        self._log_skip(
            SkipLogEntry(
                node,
                details,
                logic.get_additional_requirements(node),
            )
        )

    @abc.abstractmethod
    def _log_skip(self, skip_entry: SkipLogEntry) -> None:
        """Internal logic for logging skipped actions."""

    @final
    def log_complete(self, state: State | None) -> None:
        """Logs the resolver completing its run."""
        if not self.should_perform_logging:
            return
        self._log_victory(state)

    @abc.abstractmethod
    def _log_victory(self, state: State | None) -> None:
        """
        Internal logic for logging completion.

        :param state: Will be `None` if the run was unsuccesful.
        """


class TextResolverLogger(ResolverLogger):
    current_indent: int

    def logger_start(self) -> None:
        super().logger_start()
        self.current_indent = 0

    @property
    def should_perform_logging(self) -> bool:
        return debug.debug_level() > debug.LogLevel.SILENT

    def _indent(self, offset: int = 0) -> str:
        return " " * (self.current_indent - offset)

    def action_string(self, details: ActionDetails | None) -> str:
        if details is None:
            return ""
        return f"[action {details.text}] "

    def print_requirement_set(self, requirement_set: RequirementSet, indent: int = 0) -> None:
        requirement_set.pretty_print(self._indent(indent), print_function=debug.print_function)

    def _log_action(self, action_entry: ActionLogEntry) -> None:
        self.current_indent += 1

        if self.should_show("Action", debug.debug_level()):
            if self.should_show("ActionEnergy", debug.debug_level()):
                for node in action_entry.path_from_previous:
                    debug.print_function(f"{self._indent(1)}: {self.node_string(node)}")

            resources = action_entry.resource_string()

            node_str = self.node_string(action_entry.location)
            action_str = self.action_string(action_entry.details)
            energy_str = (
                f" [{action_entry.state_string}]" if self.should_show("ActionEnergy", debug.debug_level()) else ""
            )

            debug.print_function(f"{self._indent(1)}> {node_str}{energy_str} for {action_str}[{resources}]")

    def _log_checking_satisfiable(
        self, actions: Iterable[tuple[ActionPriority, GraphOrClassicNode | ResourceNode, DamageState]]
    ) -> None:
        if self.should_show("CheckSatisfiable", debug.debug_level()):
            if actions:
                debug.print_function(f"{self._indent()}# Satisfiable Actions")
                for priority, action, _ in actions:
                    debug.print_function(f"{self._indent(-1)}= [{priority.name}] {self.node_string(action)}")
            else:
                debug.print_function(f"{self._indent()}# No Satisfiable Actions")

    def _log_rollback(self, rollback_entry: RollbackLogEntry) -> None:
        if self.should_show("Rollback", debug.debug_level()):
            node_str = self.node_string(rollback_entry.location)
            action_str = self.action_string(rollback_entry.details)
            debug.print_function(f"{self._indent()}* Rollback {node_str} {action_str}")

            show_additional = self.should_show("RollbackAdditional", debug.debug_level())
            debug.print_function(
                "{}Had action? {}; Possible Action? {}{}".format(
                    self._indent(-1),
                    rollback_entry.has_action,
                    rollback_entry.possible_action,
                    "; Additional Requirements:" if show_additional else "",
                )
            )
            if show_additional:
                self.print_requirement_set(rollback_entry.additional_requirements, -1)

        self.current_indent -= 1

    def _log_skip(self, skip_entry: SkipLogEntry) -> None:
        if self.should_show("Skip", debug.debug_level()):
            node_str = self.node_string(skip_entry.location)
            action_str = self.action_string(skip_entry.details)
            base_log = f"{self._indent()}* Skip {node_str} {action_str}"

            previous = self.last_printed_additional.get(skip_entry.location.node_index)
            if previous == skip_entry.additional_requirements:
                debug.print_function(f"{base_log}, same additional")
            else:
                debug.print_function(f"{base_log}, missing additional:")
                self.print_requirement_set(skip_entry.additional_requirements, -1)
                self.last_printed_additional[skip_entry.location.node_index] = skip_entry.additional_requirements

    def _log_victory(self, state: State | None) -> None:
        return
