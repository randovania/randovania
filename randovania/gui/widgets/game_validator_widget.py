from __future__ import annotations

import asyncio
import re
import time
from typing import TYPE_CHECKING, NamedTuple

from PySide6 import QtGui, QtWidgets
from qasync import asyncSlot

from randovania.gui.generated.game_validator_widget_ui import Ui_GameValidatorWidget
from randovania.gui.lib import common_qt_lib, signal_handling
from randovania.resolver import debug, resolver
from randovania.resolver.logging import ActionType, GenericActionDetails, PickupActionDetails, ResolverLogger

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.resource_node import ResourceNode
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.layout_description import LayoutDescription
    from randovania.resolver.damage_state import DamageState
    from randovania.resolver.logging import ActionDetails, ActionLogEntry, RollbackLogEntry, SkipLogEntry
    from randovania.resolver.state import State


class IndentedWidget(NamedTuple):
    indent: int
    item: QtWidgets.QTreeWidgetItem
    action_type: ActionType | str = ActionType.OTHER
    action_visibility_type: str | None = None


_LABELS = ["Node", "Type", "Action", "Energy", "Resources"]
LABEL_IDS = {label: i for i, label in enumerate(_LABELS)}

action_type_re = re.compile(r"^(?P<type>.*?) - (?P<action>.*?)$")


def get_brush_for_action(action_type: ActionType | str) -> QtGui.QBrush:
    ACTION_COLORS: dict[str, QtGui.QColor] = {
        ActionType.MAJOR_PICKUP: QtGui.QColorConstants.Cyan,
        ActionType.MINOR_PICKUP: QtGui.QColorConstants.DarkCyan,
        ActionType.EVENT: QtGui.QColorConstants.Magenta,
        ActionType.LOCK: QtGui.QColorConstants.Green,
        ActionType.HINT: QtGui.QColorConstants.Yellow,
        ActionType.OTHER: QtGui.QColorConstants.Red,
    }
    return QtGui.QBrush(ACTION_COLORS.get(action_type, ACTION_COLORS[ActionType.OTHER]))


async def _run_validator(logger: ResolverLogger, debug_level: debug.LogLevel, layout: LayoutDescription) -> str:
    configuration: BaseConfiguration = layout.get_preset(0).configuration
    patches = layout.all_patches[0]

    before = time.perf_counter()
    with debug.with_level(debug_level):
        final_state_by_resolve = await resolver.resolve(
            configuration=configuration,
            patches=patches,
            logger=logger,
        )
    after = time.perf_counter()

    return "Took {:.3f} seconds. Game is {}.".format(
        after - before, "possible" if final_state_by_resolve is not None else "impossible"
    )


class GameValidatorWidget(QtWidgets.QWidget, Ui_GameValidatorWidget):
    _current_task: asyncio.Task | None

    def __init__(self, layout: LayoutDescription, players: PlayersConfiguration):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.layout_description = layout
        self.players = players
        self._current_task = None
        self._current_tree: list[IndentedWidget] = []

        self.start_button.clicked.connect(self.on_start_button)

        configs: list[BaseConfiguration] = [preset.configuration for preset in layout.all_presets]
        self._action_filters = {
            "Major": True,
            "Minor": False,
            "Event": True,
            "Hint": False,
            "Lock": configs[players.player_index].dock_rando.is_enabled(),
        }
        self._last_run_filters: dict[str, bool] | None = None

        def init_filter(check: QtWidgets.QCheckBox, action_type: str) -> None:
            check.setChecked(self._action_filters[action_type])
            signal_handling.on_checked(check, self._set_action_filter(action_type))

        init_filter(self.show_pickups_check, "Major")
        init_filter(self.show_minors_check, "Minor")
        init_filter(self.show_events_check, "Event")
        init_filter(self.show_hints_check, "Hint")
        init_filter(self.show_locks_check, "Lock")

        self.logger = ValidatorWidgetResolverLogger(self)

        for level in sorted(self.logger.log_levels_used):
            self.verbosity_combo.addItem(level.name.capitalize(), level)

        self.verbosity_combo.setCurrentIndex(self.verbosity_combo.findData(debug.LogLevel.NORMAL))

        self._last_run_verbosity: int | None = None
        signal_handling.on_combo(self.verbosity_combo, self._set_verbosity)
        self._verbosity: debug.LogLevel = self.verbosity_combo.currentData()

    def stop_validator(self) -> None:
        if self._current_task is not None:
            self._current_task.cancel()

    def _update_needs_refresh(self) -> None:
        need_refresh_filters = not (self._last_run_filters is None or self._action_filters == self._last_run_filters)
        need_refresh_verbosity = not (self._last_run_verbosity is None or self._verbosity == self._last_run_verbosity)

        if need_refresh_filters or need_refresh_verbosity:
            text = "Please re-run the resolver to update the data"
        else:
            text = ""

        self.needs_refresh_label.setText(text)

    def _set_action_filter(self, action_type: str) -> Callable[[bool], None]:
        def bound(value: bool) -> None:
            self._action_filters[action_type] = value
            self._update_needs_refresh()

        return bound

    def _set_verbosity(self, value: debug.LogLevel) -> None:
        self._verbosity = value
        self._update_needs_refresh()

    def should_item_be_visible(self, widget: IndentedWidget) -> bool:
        action_type = widget.action_visibility_type or widget.action_type
        if action_type is None:
            return True
        return self._action_filters.get(action_type, True)

    def update_item_visibility(self, widget: IndentedWidget) -> None:
        hide = not self.should_item_be_visible(widget)
        widget.item.setHidden(hide)

    def tree_item(
        self,
        *,
        node: str,
        action_type: str,
        action_details: str,
        energy: str = "",
        resources: str = "",
    ) -> QtWidgets.QTreeWidgetItem:
        item = QtWidgets.QTreeWidgetItem()
        item.setText(LABEL_IDS["Node"], node)
        item.setText(LABEL_IDS["Type"], action_type)
        item.setText(LABEL_IDS["Action"], action_details)
        item.setText(LABEL_IDS["Energy"], energy)
        item.setText(LABEL_IDS["Resources"], resources)
        return item

    def add_simple_log_entry(self, text: str, indent: int) -> None:
        item = self.tree_item(node=text, action_type="", action_details="")
        widget = IndentedWidget(indent, item)
        self.add_log_entry(widget)

    def add_log_entry(
        self,
        widget: IndentedWidget,
        identifier: NodeIdentifier | None = None,
    ) -> None:
        scrollbar = self.log_widget.verticalScrollBar()
        should_autoscroll = scrollbar.value() == scrollbar.maximum()

        while self._current_tree[-1].indent >= widget.indent:
            self._current_tree.pop().item.setExpanded(False)

        if self.should_item_be_visible(widget) and identifier is not None:
            if len(self._current_tree) == 2:
                region_item = self._current_tree[-1].item

                if region_item.text(LABEL_IDS["Node"]) != identifier.region:
                    self._current_tree.pop()

            if len(self._current_tree) == 1:
                region_item = QtWidgets.QTreeWidgetItem(self._current_tree[-1].item)
                region_item.setText(LABEL_IDS["Node"], identifier.region)
                self._current_tree.append(IndentedWidget(-1, region_item))

                region_item.setExpanded(True)

        parent = self._current_tree[-1].item
        parent.addChild(widget.item)

        widget.item.setForeground(LABEL_IDS["Type"], get_brush_for_action(widget.action_type))
        widget.item.setBackground(LABEL_IDS["Type"], QtGui.QColor(32, 33, 36))  # ugly in light mode, but visible

        self.update_item_visibility(widget)
        self._current_tree.append(widget)

        if should_autoscroll:
            self.log_widget.scrollToBottom()

    def resize_columns(self) -> None:
        for label in ("Node", "Action", "Resources", "Energy"):
            self.log_widget.resizeColumnToContents(LABEL_IDS[label])

    @asyncSlot()
    async def on_start_button(self) -> None:
        if self._current_task is not None:
            return self.stop_validator()

        self._last_run_filters = dict(self._action_filters)
        self.needs_refresh_label.setText("")

        self._last_run_verbosity = self._verbosity

        self.start_button.setText("Stop")
        self.status_label.setText("Running...")

        self.log_widget.clear()
        self.log_widget.setColumnCount(len(LABEL_IDS))
        self.log_widget.setHeaderLabels(list(LABEL_IDS))

        self.log_widget.setColumnHidden(LABEL_IDS["Energy"], self._verbosity < 2)
        self.log_widget.setColumnHidden(LABEL_IDS["Resources"], self._verbosity < 2)

        default_col_sizes = {
            LABEL_IDS["Node"]: 350,
            LABEL_IDS["Type"]: 50,
        }
        if self._verbosity >= debug.LogLevel.HIGH:
            default_col_sizes.update(
                {
                    LABEL_IDS["Action"]: 200,
                    LABEL_IDS["Energy"]: 60,
                }
            )

        for column, size in default_col_sizes.items():
            self.log_widget.setColumnWidth(column, size)

        self._current_tree = [IndentedWidget(-2, self.log_widget)]

        self._current_task = asyncio.create_task(_run_validator(self.logger, self._verbosity, self.layout_description))
        try:
            time_consumed = await self._current_task
            self.status_label.setText(time_consumed)
        except asyncio.CancelledError:
            self.status_label.setText("Cancelled!")
        finally:
            self.start_button.setText("Start")
            self._current_task = None

    def tree_as_lines(self) -> Iterator[str]:
        """Iterates each item in the log tree as lines of text."""

        def inner_print(item: QtWidgets.QTreeWidgetItem, indent: int = 0) -> Iterator[str]:
            text = "{}{} | {} | {}".format(
                " " * indent * 2,
                item.text(LABEL_IDS["Node"]),
                item.text(LABEL_IDS["Type"]),
                item.text(LABEL_IDS["Action"]),
            )
            if self._verbosity >= debug.LogLevel.HIGH:
                text = "{} | {} | {}".format(
                    text,
                    item.text(LABEL_IDS["Energy"]),
                    item.text(LABEL_IDS["Resources"]),
                )
            yield text
            for i in range(item.childCount()):
                yield from inner_print(item.child(i), indent + 1)

        for i in range(self.log_widget.topLevelItemCount()):
            yield from inner_print(self.log_widget.topLevelItem(i))


class ValidatorWidgetResolverLogger(ResolverLogger):
    def __init__(self, validator_widget: GameValidatorWidget) -> None:
        self.validator_widget = validator_widget

    def logger_start(self) -> None:
        super().logger_start()
        self.log_level = self.validator_widget._verbosity

    def action_type_and_text(self, details: ActionDetails) -> tuple[str, str]:
        if isinstance(details, PickupActionDetails):
            action_type = details.action_type.value
            if details.target is None:
                action_text = "Nothing"
            else:
                action_text = details.target.pickup.name
                if self.validator_widget.layout_description.world_count > 1:
                    player_name = self.validator_widget.players.player_names[details.target.player]
                    action_text = f"{player_name}'s {action_text}"

        else:
            assert isinstance(details, GenericActionDetails)
            action_type_match = action_type_re.match(details.text)
            if action_type_match is None:
                return "Other", details.text

            action_text = action_type_match.group("action")
            action_type = action_type_match.group("type")

        return action_type, action_text

    def _log_action(self, action_entry: ActionLogEntry) -> None:
        if not self.should_show("Action", self.log_level):
            return

        if self.should_show("ActionPath", self.log_level):
            for node in action_entry.path_from_previous:
                self.validator_widget.add_simple_log_entry(
                    f"↪ {node.identifier.as_string}",
                    indent=1,
                )

        if action_entry.details is not None:
            action_type, action_text = self.action_type_and_text(action_entry.details)
        else:
            action_type, action_text = "Start", ""

        item = self.validator_widget.tree_item(
            node=action_entry.location.full_name(False),
            action_type=action_type,
            action_details=action_text,
            energy=f"{action_entry.simple_state}",
            resources=action_entry.resource_string(full_types=True),
        )
        widget = IndentedWidget(0, item, action_type)

        self.validator_widget.add_log_entry(widget, action_entry.location.identifier)

    def _log_checking_satisfiable(self, actions: Iterable[tuple[ResourceNode, DamageState]]) -> None:
        if not self.should_show("CheckSatisfiable", self.log_level):
            return

        if not actions:
            self.validator_widget.add_simple_log_entry("No satisfiable actions", 1)
            return

        self.validator_widget.add_simple_log_entry("Satisfiable actions", 1)

        for node, _ in actions:
            self.validator_widget.add_simple_log_entry(
                f"• {node.identifier.as_string}",
                indent=2,
            )

    def _log_rollback_or_skip(
        self,
        entry: RollbackLogEntry | SkipLogEntry,
        negation_type: str,
        extra_text: str = "",
        *,
        extra_text_font: QtGui.QFont | None = None,
        show_additional_requirements: bool = True,
    ) -> None:
        item = self.validator_widget.tree_item(
            node=f"{negation_type} {entry.location.full_name(False)}",
            action_type=negation_type,
            action_details=extra_text,
        )
        if extra_text_font is not None:
            item.setFont(LABEL_IDS["Action"], extra_text_font)

        if entry.details is None:
            underlying_action_type = ActionType.OTHER
        else:
            underlying_action_type = entry.details.action_type

        widget = IndentedWidget(0, item, ActionType.OTHER, underlying_action_type)
        self.validator_widget.add_log_entry(widget, entry.location.identifier)

        if show_additional_requirements:
            self.validator_widget.add_simple_log_entry("Additional Requirement Alternatives", 1)

            for line in entry.additional_requirements.as_lines:
                self.validator_widget.add_simple_log_entry(f"• {line}", 2)

    def _log_rollback(self, rollback_entry: RollbackLogEntry) -> None:
        if not self.should_show("Rollback", self.log_level):
            return

        extra_text = f"Had action? {rollback_entry.has_action}; Possible action? {rollback_entry.possible_action}"

        self._log_rollback_or_skip(
            rollback_entry,
            "Rollback",
            extra_text,
            show_additional_requirements=self.should_show("RollbackAdditional", self.log_level),
        )

    def _log_skip(self, skip_entry: SkipLogEntry) -> None:
        if not self.should_show("Skip", self.log_level):
            return

        previous = self.last_printed_additional.get(skip_entry.location)
        if previous == skip_entry.additional_requirements:
            extra_text = "Same additional"
            font = None
        else:
            extra_text = "New additional"
            font = QtGui.QFont(self.validator_widget.font())
            font.setBold(True)
            self.last_printed_additional[skip_entry.location] = skip_entry.additional_requirements

        self._log_rollback_or_skip(
            skip_entry,
            "Skip",
            extra_text,
            extra_text_font=font,
        )

    def _log_victory(self, state: State | None) -> None:
        if not self.should_show("Completion", self.log_level):
            return

        if state is None:
            action_type = "Failure"
            details = "Game is impossible"
        else:
            action_type = "Success"
            details = "Game is possible"

        item = self.validator_widget.tree_item(
            node="Playthrough Complete",
            action_type=action_type,
            action_details=details,
        )

        widget = IndentedWidget(0, item)
        self.validator_widget.add_log_entry(widget)
        self.validator_widget.resize_columns()
