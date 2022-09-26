import asyncio
import time

from PySide6 import QtWidgets
from qasync import asyncSlot

from randovania.gui.generated.game_validator_widget_ui import Ui_GameValidatorWidget
from randovania.gui.lib import common_qt_lib
from randovania.layout.layout_description import LayoutDescription
from randovania.resolver import debug, resolver


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
            )
        after = time.perf_counter()

        return "Took {:.3f} seconds. Game is {}.".format(
            after - before,
            "possible" if final_state_by_resolve is not None else "impossible"
        )
    finally:
        debug.print_function = old_print_function


class GameValidatorWidget(QtWidgets.QWidget, Ui_GameValidatorWidget):
    _current_task: asyncio.Task | None

    def __init__(self, layout: LayoutDescription):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.layout = layout
        self._current_task = None

        self.start_button.clicked.connect(self.on_start_button)

    def stop_validator(self):
        if self._current_task is not None:
            return self._current_task.cancel()

    @asyncSlot()
    async def on_start_button(self):
        if self._current_task is not None:
            return self.stop_validator()

        self.start_button.setText("Stop")
        self.status_label.setText("Running...")

        self.log_widget.clear()
        self.log_widget.setColumnCount(1)
        self.log_widget.setHeaderLabels(["Steps"])

        current_tree = [
            (-1, self.log_widget)
        ]

        def write_to_log(*a):
            scrollbar = self.log_widget.verticalScrollBar()
            autoscroll = scrollbar.value() == scrollbar.maximum()

            message = "    ".join(str(t) for t in a)
            stripped = message.lstrip()
            indent = len(message) - len(stripped)

            # Remove any leading >
            if stripped.startswith("> "):
                stripped = stripped[2:]

            while current_tree[-1][0] >= indent:
                current_tree.pop()[1].setExpanded(False)

            item = QtWidgets.QTreeWidgetItem(current_tree[-1][1])
            item.setText(0, stripped)
            item.setExpanded(True)
            current_tree.append((indent, item))

            self.log_widget.resizeColumnToContents(0)
            if autoscroll:
                self.log_widget.scrollToBottom()
                bar: QtWidgets.QScrollBar = self.log_widget.horizontalScrollBar()
                bar.setValue(bar.maximum())

        self._current_task = asyncio.create_task(_run_validator(
            write_to_log, self.verbosity_combo.currentIndex(), self.layout
        ))
        try:
            time_consumed = await self._current_task
            self.status_label.setText(time_consumed)
        except asyncio.CancelledError:
            self.status_label.setText("Cancelled!")
        finally:
            self.start_button.setText("Start")
            self._current_task = None

