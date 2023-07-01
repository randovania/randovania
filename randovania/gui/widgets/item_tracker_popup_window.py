import functools
import typing
from pathlib import Path

from PySide6 import QtWidgets, QtGui

from randovania.gui.lib import common_qt_lib
from randovania.gui.widgets.item_tracker_widget import ItemTrackerWidget
from randovania.lib import json_lib


class ItemTrackerPopupWindow(QtWidgets.QWidget):
    def __init__(self, title: str, themes: dict[str, Path], on_close: typing.Callable[[], None]):
        super().__init__(None)
        common_qt_lib.set_default_window_icon(self)
        self.on_close = on_close

        self.setWindowTitle(title)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.main_layout)

        tracker_layout = None
        self.menu_bar = QtWidgets.QMenuBar(self)

        menu = self.menu_bar.addMenu("Select Theme")
        group = QtGui.QActionGroup(menu)
        for theme, theme_path in themes.items():
            action = menu.addAction(theme)
            action.setCheckable(True)
            action.triggered.connect(functools.partial(self._on_select_theme, theme_path))
            action.setActionGroup(group)

            if tracker_layout is None:
                tracker_layout = json_lib.read_path(theme_path)
                action.setChecked(True)

        self.main_layout.addWidget(self.menu_bar)
        self.item_tracker = ItemTrackerWidget(tracker_layout)
        self.item_tracker.update_state({})
        self.main_layout.addWidget(self.item_tracker)

    def _on_select_theme(self, path: Path):
        self.change_tracker_layout(json_lib.read_path(path))

    def change_tracker_layout(self, tracker_layout: dict):
        self.item_tracker.deleteLater()
        current_state = self.item_tracker.current_state
        self.item_tracker = ItemTrackerWidget(tracker_layout)
        self.item_tracker.update_state(current_state)
        self.main_layout.addWidget(self.item_tracker)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.on_close()
        return super().closeEvent(event)
