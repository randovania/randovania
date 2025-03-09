from __future__ import annotations

import asyncio
import re
import time
from typing import TYPE_CHECKING, NamedTuple

from PySide6 import QtWidgets
from qasync import asyncSlot

from randovania.gui.generated.game_validator_widget_ui import Ui_GameValidatorWidget
from randovania.gui.lib import common_qt_lib, signal_handling
from randovania.resolver import debug, resolver

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.layout_description import LayoutDescription


class IndentedWidget(NamedTuple):
    indent: int
    item: QtWidgets.QTreeWidgetItem
    action_type: str | None = None


ACTION_CHAR = ">"
PATH_CHAR = ":"
SATISFIABLE_CHAR = "="
COMMENT_CHAR = "#"
SKIP_ROLLBACK_CHAR = "*"

action_re = re.compile(
    r"^(?P<node>.+?) (?:\[(?P<energy>\d+?/\d+?) Energy] )?for (?:\[action (?P<action>.*?)] )?(?P<resources>\[.*?])$"
)
pickup_action_re = re.compile(r"^World (?P<world_num>\d+?)'s (?P<pickup_name>.*?)$")
action_type_re = re.compile(r"^(?P<type>.*?) - (?P<action>.*?)$")


async def _run_validator(write_to_log, debug_level: int, layout: LayoutDescription):
    old_print_function = debug.print_function
    try:
        debug.print_function = write_to_log

        configuration = layout.get_preset(0).configuration
        patches = layout.all_patches[0]

        before = time.perf_counter()
        with debug.with_level(debug_level):
            final_state_by_resolve = await resolver.resolve(
                configuration=configuration,
                patches=patches,
                fully_indent_log=False,
            )
        after = time.perf_counter()

        return "Took {:.3f} seconds. Game is {}.".format(
            after - before, "possible" if final_state_by_resolve is not None else "impossible"
        )
    finally:
        debug.print_function = old_print_function


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

        self._labels = ["Node", "Type", "Action", "Energy", "Resources"]
        self._label_ids = {label: i for i, label in enumerate(self._labels)}

        self.start_button.clicked.connect(self.on_start_button)

        configs: list[BaseConfiguration] = [preset.configuration for preset in layout.all_presets]
        self._action_filters = {
            "Pickup": True,
            "Event": True,
            "Hint": False,
            "Lock": configs[players.player_index].dock_rando.is_enabled(),
        }
        self._last_run_filters: dict[str, bool] = None

        def init_filter(check: QtWidgets.QCheckBox, action_type: str) -> None:
            check.setChecked(self._action_filters[action_type])
            signal_handling.on_checked(check, self._set_action_filter(action_type))

        init_filter(self.show_pickups_check, "Pickup")
        init_filter(self.show_events_check, "Event")
        init_filter(self.show_hints_check, "Hint")
        init_filter(self.show_locks_check, "Lock")

    def stop_validator(self):
        if self._current_task is not None:
            return self._current_task.cancel()

    def _set_action_filter(self, action_type: str) -> Callable[[bool], None]:
        def bound(value: bool) -> None:
            self._action_filters[action_type] = value

            if self._last_run_filters is None or self._action_filters == self._last_run_filters:
                self.needs_refresh_label.setText("")
            else:
                self.needs_refresh_label.setText("Please re-run the resolver to update the filters")

        return bound

    def update_item_visibility(self, widget: IndentedWidget) -> None:
        if widget.action_type is None:
            return
        hide = not self._action_filters.get(widget.action_type, True)
        widget.item.setHidden(hide)

    @asyncSlot()
    async def on_start_button(self):
        if self._current_task is not None:
            return self.stop_validator()

        self._last_run_filters = dict(self._action_filters)
        self.needs_refresh_label.setText("")

        verbosity = self.verbosity_combo.currentIndex()

        self.start_button.setText("Stop")
        self.status_label.setText("Running...")

        self.log_widget.clear()
        self.log_widget.setColumnCount(len(self._labels))
        self.log_widget.setHeaderLabels(self._labels)

        self.log_widget.setColumnHidden(self._label_ids["Energy"], verbosity < 2)
        self.log_widget.setColumnHidden(self._label_ids["Resources"], verbosity < 2)

        self._current_tree = [IndentedWidget(-1, self.log_widget)]  # type: ignore[assignment]

        def write_to_log(*a):
            scrollbar = self.log_widget.verticalScrollBar()
            autoscroll = scrollbar.value() == scrollbar.maximum()

            message = "    ".join(str(t) for t in a)
            stripped = message.lstrip()
            indent = len(message) - len(stripped)

            print(message)

            leading_char = stripped[0]

            # Extra indent
            leading_chars_to_indent = (COMMENT_CHAR, PATH_CHAR, SATISFIABLE_CHAR)
            if leading_char in leading_chars_to_indent:
                indent += 1

            # Remove leading chars
            leading_chars_to_remove = (ACTION_CHAR, PATH_CHAR, SATISFIABLE_CHAR)
            if leading_char in leading_chars_to_remove:
                stripped = stripped[2:]

            while self._current_tree[-1].indent >= indent:
                self._current_tree.pop().item.setExpanded(False)

            if indent == 0:
                parent = self.log_widget
            else:
                parent = self._current_tree[-1].item

            item = QtWidgets.QTreeWidgetItem(parent)

            if leading_char == ACTION_CHAR:
                match = action_re.match(stripped)
                assert match is not None
                groups = match.groupdict()

                item.setText(self._label_ids["Node"], groups["node"])
                item.setText(self._label_ids["Resources"], groups["resources"])
                item.setText(self._label_ids["Energy"], groups.get("energy", ""))

                action = groups["action"]
                if action is not None:
                    if action.startswith("World"):
                        pickup_match = pickup_action_re.match(action)
                        assert pickup_match is not None

                        player = int(pickup_match.group("world_num"))
                        pickup = pickup_match.group("pickup_name")

                        if self.layout_description.generator_parameters.world_count == 1:
                            action = pickup
                        else:
                            action = f"{self.players.player_names[player]}'s {pickup}"

                        action = f"Pickup - {action}"

                    action_type_match = action_type_re.match(action)
                    assert action_type_match is not None

                    item.setText(self._label_ids["Action"], action_type_match.group("action"))

                    action = action_type_match.group("type")
                    item.setText(self._label_ids["Type"], action)
                    widget = IndentedWidget(indent, item, action)
                else:
                    item.setText(self._label_ids["Type"], "Start")
                    widget = IndentedWidget(indent, item)
            else:
                item.setText(0, stripped)
                widget = IndentedWidget(indent, item)

            item.setExpanded(indent == 0)

            self.update_item_visibility(widget)
            self._current_tree.append(widget)

            for label in ("Node", "Action", "Resources"):
                self.log_widget.resizeColumnToContents(self._label_ids[label])
            if autoscroll:
                self.log_widget.scrollToBottom()

        self._current_task = asyncio.create_task(_run_validator(write_to_log, verbosity, self.layout_description))
        try:
            time_consumed = await self._current_task
            self.status_label.setText(time_consumed)
        except asyncio.CancelledError:
            self.status_label.setText("Cancelled!")
        finally:
            self.start_button.setText("Start")
            self._current_task = None
