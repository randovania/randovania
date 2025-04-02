from __future__ import annotations

import asyncio
import re
import time
from typing import TYPE_CHECKING, Any, NamedTuple

from PySide6 import QtGui, QtWidgets
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
    action_visibility_type: str | None = None


_LABELS = ["Node", "Type", "Action", "Energy", "Resources"]
LABEL_IDS = {label: i for i, label in enumerate(_LABELS)}


ACTION_CHAR = ">"
PATH_CHAR = ":"
SATISFIABLE_CHAR = "="
COMMENT_CHAR = "#"
SKIP_ROLLBACK_CHAR = "*"

location_pattern = r"(?P<region>.+?)/(?P<area>.+?)/(?P<node>.+?)"
action_pattern = r"\[action (?P<action>.*?)]"

action_re = re.compile(
    f"^{location_pattern} "
    r"(?:\[(?P<energy>\d+?/\d+?) Energy] )?"
    f"for (?:{action_pattern} )?"
    r"(?P<resources>\[.*?])$"
)
rollback_skip_re = re.compile(
    r"^(?P<action_type>.*?) "
    f"{location_pattern} "
    f"{action_pattern} ?"
    r"(?:, (?P<additional>.*?))?$"
)

pickup_action_re = re.compile(r"^World (?P<world_num>\d+?)'s (?P<pickup_name>.*?)$")
action_type_re = re.compile(r"^(?P<type>.*?) - (?P<action>.*?)$")


def get_brush_for_action(action_type: str | None) -> QtGui.QBrush:
    ACTION_COLORS = {
        "Pickup": QtGui.QColorConstants.Cyan,
        "Major": QtGui.QColorConstants.Cyan,
        "Minor": QtGui.QColorConstants.DarkCyan,
        "Event": QtGui.QColorConstants.Magenta,
        "Lock": QtGui.QColorConstants.Green,
        "Hint": QtGui.QColorConstants.Yellow,
        None: QtGui.QColorConstants.Red,
    }
    return QtGui.QBrush(ACTION_COLORS.get(action_type, ACTION_COLORS[None]))


async def _run_validator(write_to_log: debug.DebugPrintFunction, debug_level: int, layout: LayoutDescription) -> str:
    old_print_function = debug.print_function
    try:
        debug.print_function = write_to_log

        configuration: BaseConfiguration = layout.get_preset(0).configuration
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

        self._last_run_verbosity: int | None = None
        for i, name in enumerate(["Silent", "Normal", "High", "Extreme"]):
            self.verbosity_combo.setItemText(i, name)
            self.verbosity_combo.setItemData(i, i)
        signal_handling.on_combo(self.verbosity_combo, self._set_verbosity)
        self._verbosity = self.verbosity_combo.currentIndex()

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

    def _set_verbosity(self, value: int) -> None:
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

        self._current_tree = [IndentedWidget(-2, self.log_widget)]

        def write_to_log(*a: Any) -> None:
            scrollbar = self.log_widget.verticalScrollBar()
            autoscroll = scrollbar.value() == scrollbar.maximum()

            message = "    ".join(str(t) for t in a)
            stripped = message.lstrip().rstrip()
            indent = len(message) - len(stripped)

            leading_char = stripped[0]

            # Extra indent
            leading_chars_to_indent = (COMMENT_CHAR, PATH_CHAR, SATISFIABLE_CHAR)
            if leading_char in leading_chars_to_indent:
                indent += 1

            # Remove indent
            leading_chars_to_dedent = (SKIP_ROLLBACK_CHAR,)
            if leading_char in leading_chars_to_dedent:
                indent -= 1

            # Remove leading chars
            leading_chars_to_remove = (ACTION_CHAR, PATH_CHAR, SATISFIABLE_CHAR, SKIP_ROLLBACK_CHAR)
            if leading_char in leading_chars_to_remove:
                stripped = stripped[2:]

            while self._current_tree[-1].indent >= indent:
                self._current_tree.pop().item.setExpanded(False)

            item = QtWidgets.QTreeWidgetItem()
            region, area, node = ("", "", "")

            def action_type_and_text(_action: str) -> tuple[str, str]:
                action_type_match = action_type_re.match(_action)
                if action_type_match is None:
                    return "Other", _action

                action_text = action_type_match.group("action")
                action_type = action_type_match.group("type")

                if (action_type in {"Major", "Minor", "Pickup"}) and action_text != "Nothing":
                    pickup_match = pickup_action_re.match(action_text)
                    assert pickup_match is not None

                    player = int(pickup_match.group("world_num"))
                    pickup = pickup_match.group("pickup_name")

                    if self.layout_description.world_count == 1:
                        action_text = pickup
                    else:
                        action_text = f"{self.players.player_names[player]}'s {pickup}"

                return action_type, action_text

            if leading_char == ACTION_CHAR:
                match = action_re.match(stripped)
                assert match is not None
                groups = match.groupdict()

                region = groups["region"]
                area = groups["area"]
                node = groups["node"]

                item.setText(LABEL_IDS["Node"], f"{area}/{node}")
                item.setText(LABEL_IDS["Resources"], groups["resources"])
                item.setText(LABEL_IDS["Energy"], groups.get("energy", ""))

                action = groups["action"]
                if action is not None:
                    action_type, action_text = action_type_and_text(action)

                    item.setText(LABEL_IDS["Type"], action_type)
                    item.setText(LABEL_IDS["Action"], action_text)

                    widget = IndentedWidget(indent, item, action_type)
                else:
                    item.setText(LABEL_IDS["Type"], "Start")
                    widget = IndentedWidget(indent, item)

            elif leading_char == SKIP_ROLLBACK_CHAR:
                rollback_skip_match = rollback_skip_re.match(stripped)
                if rollback_skip_match is None:
                    # This happens when rolling back an action that isn't a Resource Node
                    # The only time this is the case is when rolling back the first action, aka it's impossible
                    return
                groups = rollback_skip_match.groupdict()

                region = groups["region"]
                area = groups["area"]
                node = groups["node"]

                action_type = groups["action_type"]

                underlying_action_type, _ = action_type_and_text(groups["action"])

                item.setText(LABEL_IDS["Node"], f"{action_type} {area}/{node}")
                item.setText(LABEL_IDS["Type"], action_type)
                if (extra := groups.get("additional")) is not None:
                    item.setText(LABEL_IDS["Action"], extra.capitalize())
                widget = IndentedWidget(indent, item, action_type, underlying_action_type)

            else:
                item.setText(0, stripped)
                widget = IndentedWidget(indent, item)

            if self.should_item_be_visible(widget) and node:
                if len(self._current_tree) == 2:
                    region_item = self._current_tree[-1].item

                    if region_item.text(LABEL_IDS["Node"]) != region:
                        self._current_tree.pop()

                if len(self._current_tree) == 1:
                    region_item = QtWidgets.QTreeWidgetItem(self._current_tree[-1].item)
                    region_item.setText(LABEL_IDS["Node"], region)
                    self._current_tree.append(IndentedWidget(-1, region_item))

                    region_item.setExpanded(True)

            parent = self._current_tree[-1].item
            parent.addChild(item)

            item.setForeground(LABEL_IDS["Type"], get_brush_for_action(widget.action_type))
            item.setBackground(LABEL_IDS["Type"], QtGui.QColor(32, 33, 36))  # ugly in light mode, but visible

            self.update_item_visibility(widget)
            self._current_tree.append(widget)

            for label in ("Node", "Action", "Resources"):
                self.log_widget.resizeColumnToContents(LABEL_IDS[label])
            if autoscroll:
                self.log_widget.scrollToBottom()

        self._current_task = asyncio.create_task(_run_validator(write_to_log, self._verbosity, self.layout_description))
        try:
            time_consumed = await self._current_task
            self.status_label.setText(time_consumed)
        except asyncio.CancelledError:
            self.status_label.setText("Cancelled!")
        finally:
            self.start_button.setText("Start")
            self._current_task = None
