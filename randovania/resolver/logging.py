from __future__ import annotations

import abc
import typing
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Literal, NamedTuple, Protocol, Self, final

from randovania.game_description.db.dock_lock_node import DockLockNode
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.event_pickup import EventPickupNode
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.resource_node import ResourceNode
from randovania.resolver import debug

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from randovania.game_description.assignment import PickupTarget
    from randovania.game_description.db.node import Node
    from randovania.game_description.requirements.requirement_set import RequirementSet
    from randovania.game_description.resources.resource_info import ResourceGainTuple
    from randovania.resolver.damage_state import DamageState
    from randovania.resolver.logic import Logic
    from randovania.resolver.state import State


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

    @staticmethod
    def from_state(state: State) -> ActionDetails | None:
        node = state.node

        if not node.is_resource_node:
            return None
        node = typing.cast("ResourceNode", node)

        if isinstance(node, EventPickupNode):
            node = node.pickup_node

        if isinstance(node, PickupNode):
            target = state.patches.pickup_assignment.get(node.pickup_index, None)
            if target is not None and target.pickup.show_in_credits_spoiler:
                action_type = ActionType.MAJOR_PICKUP
            else:
                action_type = ActionType.MINOR_PICKUP
            return PickupActionDetails(action_type, target)

        text = node.name

        if isinstance(node, EventNode):
            action_type = ActionType.EVENT
        elif isinstance(node, DockLockNode):
            action_type = ActionType.LOCK
        elif isinstance(node, HintNode):
            action_type = ActionType.HINT
            if not text.startswith("Hint - "):
                text = f"Hint - {text}"
        else:
            action_type = ActionType.OTHER

        return GenericActionDetails(action_type, text)


class GenericActionDetails(NamedTuple):
    action_type: ActionType
    text: str


class PickupActionDetails(NamedTuple):
    action_type: Literal[ActionType.MAJOR_PICKUP, ActionType.MINOR_PICKUP]
    target: PickupTarget | None

    @property
    def text(self) -> str:
        if self.target is None:
            return f"{ActionType.MINOR_PICKUP.value} - Nothing"
        return f"{self.action_type.value} - {self.target}"


class ActionLogEntry(NamedTuple):
    location: Node
    state_string: str
    details: ActionDetails | None
    resources: ResourceGainTuple
    path_from_previous: tuple[Node, ...]

    def should_show(self, log_level: int) -> bool:
        return log_level > 0

    def should_show_path(self, log_level: int) -> bool:
        return log_level >= 3

    @classmethod
    def from_state(cls, state: State) -> Self:
        resources = ()
        if isinstance(state.node, ResourceNode):
            context_state = state.previous_state or state
            resources = tuple(state.node.resource_gain_on_collect(context_state.node_context()))

        return cls(
            state.node,
            state.game_state_debug_string(),
            ActionDetails.from_state(state),
            resources,
            state.path_from_previous_state,
        )


class RollbackLogEntry(NamedTuple):
    location: Node
    details: ActionDetails | None
    has_action: bool
    possible_action: bool
    additional_requirements: RequirementSet

    def should_show(self, log_level: int) -> bool:
        return log_level > 0

    def should_show_reqs(self, log_level: int) -> bool:
        return log_level > 1 and self.additional_requirements


class SkipLogEntry(NamedTuple):
    location: Node
    details: ActionDetails
    additional_requirements: RequirementSet

    def should_show(self, log_level: int) -> bool:
        return log_level > 1


LogFeature = Literal[
    "Action",
    "ActionPath",
    "ActionEnergy",
    "Rollback",
    "RollbackAdditional",
    "Skip",
    "CheckSatisfiable",
]


class ResolverLogger(abc.ABC):
    last_printed_additional: dict[Node, RequirementSet]

    def logger_start(self) -> None:
        """Initialize the logger for a new resolver run."""
        self.last_printed_additional = {}

    def node_string(self, node: Node, with_region: bool = True) -> str:
        """Standard display format for nodes."""
        return node.full_name(with_region=with_region) if node is not None else "None"

    @cached_property
    def _visible_features(self) -> Mapping[int, frozenset[LogFeature]]:
        """Which features should be displayed at each log level"""
        visibility: dict[int, frozenset[LogFeature]] = {}

        # Silent
        visibility[0] = frozenset()

        # Normal
        visibility[1] = visibility[0] | {
            "Action",
            "Rollback",
        }
        # High
        visibility[2] = visibility[1] | {
            "ActionEnergy",
            "RollbackAdditional",
            "Skip",
            "CheckSatisfiable",
        }

        # Extreme
        visibility[3] = visibility[2] | {
            "ActionPath",
        }

        return visibility

    def should_show(self, feature: LogFeature, log_level: int) -> bool:
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
        if not self.should_perform_logging():
            return

        resources = ()
        if isinstance(state.node, ResourceNode):
            context_state = state.previous_state or state
            resources = tuple(state.node.resource_gain_on_collect(context_state.node_context()))

        self._log_action(
            ActionLogEntry(
                state.node,
                state.game_state_debug_string(),
                ActionDetails.from_state(state),
                resources,
                state.path_from_previous_state,
            )
        )

    @abc.abstractmethod
    def _log_action(self, action_entry: ActionLogEntry) -> None:
        """Internal logic for logging actions."""
        ...

    @final
    def log_checking_satisfiable(self, actions: Iterable[tuple[ResourceNode, DamageState]]) -> None:
        """Logs a list of satisfiable actions at this stage in the resolver process."""
        if not self.should_perform_logging():
            return
        self._log_checking_satisfiable(actions)

    @abc.abstractmethod
    def _log_checking_satisfiable(self, actions: Iterable[tuple[ResourceNode, DamageState]]) -> None:
        """Internal logic for logging checking satisifiable actions."""
        ...

    @final
    def log_rollback(self, state: State, has_action: bool, possible_action: bool, logic: Logic) -> None:
        """Logs an action being rolled back by the resolver."""
        if not self.should_perform_logging():
            return
        self._log_rollback(
            RollbackLogEntry(
                state.node,
                ActionDetails.from_state(state),
                has_action,
                possible_action,
                logic.get_additional_requirements(state.node),
            )
        )

    @abc.abstractmethod
    def _log_rollback(self, rollback_entry: RollbackLogEntry) -> None:
        """Internal logic for logging rollbacks."""
        ...

    @final
    def log_skip(self, node: Node, state: State, logic: Logic) -> None:
        """
        Logs an action being skipped by the resolver
        because of missing requirements.
        """
        if not self.should_perform_logging():
            return
        self._log_skip(
            SkipLogEntry(
                node,
                ActionDetails.from_state(state),
                logic.get_additional_requirements(node),
            )
        )

    @abc.abstractmethod
    def _log_skip(self, skip_entry: SkipLogEntry) -> None:
        """Internal logic for logging skipped actions."""
        ...


class TextResolverLogger(ResolverLogger):
    current_indent: int

    def logger_start(self) -> None:
        super().logger_start()
        self.current_indent = 0

    @property
    def should_perform_logging(self) -> bool:
        return debug.debug_level() > 0

    def _indent(self, offset: int = 0) -> str:
        return " " * (self.current_indent - offset)

    def action_string(self, details: ActionDetails | None) -> str:
        if details is None:
            return ""
        return f"[action {details.text}] "

    def print_requirement_set(self, requirement_set: RequirementSet, indent: int = 0):
        requirement_set.pretty_print(self._indent(indent), print_function=debug.print_function)

    def _log_action(self, action_entry: ActionLogEntry) -> None:
        self.current_indent += 1

        if self.should_show("Action", debug.debug_level()):
            if self.should_show("ActionEnergy", debug.debug_level()):
                for node in action_entry.path_from_previous:
                    debug.print_function(f"{self._indent(1)}: {self.node_string(node)}")

            resources: list[str] = []
            for resource, quantity in action_entry.resources:
                text = f"{resource.resource_type.name[0]}: {resource.long_name}"
                if quantity > 1:
                    text += f" x{quantity}"
                resources.append(text)

            node_str = self.node_string(action_entry.location)
            action_str = self.action_string(action_entry.details)
            energy_str = (
                f" [{action_entry.state_string}]" if self.should_show("ActionEnergy", debug.debug_level()) else ""
            )

            debug.print_function(f"{self._indent(1)}> {node_str}{energy_str} for {action_str}{resources}")

    def _log_checking_satisfiable(self, actions: Iterable[tuple[ResourceNode, DamageState]]) -> None:
        if self.should_show("CheckSatisfiable", debug.debug_level()):
            if actions:
                debug.print_function(f"{self._indent()}# Satisfiable Actions")
                for action, _ in actions:
                    debug.print_function(f"{self._indent(-1)}= {self.node_string(action)}")
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

            previous = self.last_printed_additional.get(skip_entry.location)
            if previous == skip_entry.additional_requirements:
                debug.print_function(f"{base_log}, same additional")
            else:
                debug.print_function(f"{base_log}, missing additional:")
                self.print_requirement_set(skip_entry.additional_requirements, -1)
                self.last_printed_additional[skip_entry.location] = skip_entry.additional_requirements
