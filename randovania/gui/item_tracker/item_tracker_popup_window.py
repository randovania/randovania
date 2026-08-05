from __future__ import annotations

import functools
import typing

from PySide6 import QtGui, QtWidgets

from randovania.game_description.resources.inventory import Inventory
from randovania.gui.item_tracker.item_tracker_widget import ItemTrackerWidget
from randovania.gui.item_tracker.tracker_assets import TrackerAssetPaths
from randovania.gui.lib import common_qt_lib


class ItemTrackerPopupWindow(QtWidgets.QWidget):
    def __init__(self, title: str, trackers: dict[str, TrackerAssetPaths], on_close: typing.Callable[[], None]) -> None:
        super().__init__(None)
        common_qt_lib.set_default_window_icon(self)
        self.on_close = on_close

        self.setWindowTitle(title)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.main_layout)

        tracker_paths = None
        self.menu_bar = QtWidgets.QMenuBar(self)

        menu = self.menu_bar.addMenu("Select Theme")
        group = QtGui.QActionGroup(menu)
        for name, paths in trackers.items():
            action = menu.addAction(name)
            action.setCheckable(True)
            action.triggered.connect(functools.partial(self._on_select_theme, paths))
            action.setActionGroup(group)

            if tracker_paths is None:
                tracker_paths = paths
                action.setChecked(True)

        assert tracker_paths is not None

        self.main_layout.addWidget(self.menu_bar)
        self.item_tracker = ItemTrackerWidget(*tracker_paths.load(), tracker_paths.assets_root)
        self.item_tracker.update_state(Inventory.empty())
        self.main_layout.addWidget(self.item_tracker)

    def _on_select_theme(self, paths: TrackerAssetPaths) -> None:
        self.change_tracker_layout(paths)

    def change_tracker_layout(self, paths: TrackerAssetPaths) -> None:
        self.item_tracker.deleteLater()
        current_state = self.item_tracker.current_state
        self.item_tracker = ItemTrackerWidget(*paths.load(), paths.assets_root)
        self.item_tracker.update_state(current_state)
        self.main_layout.addWidget(self.item_tracker)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.on_close()
        return super().closeEvent(event)
