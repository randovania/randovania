import json
import logging
from pathlib import Path

from PySide6 import QtWidgets, QtGui, QtCore
from qasync import asyncSlot

from randovania import get_data_path
from randovania.game_connection.connection_base import GameConnectionStatus
from randovania.game_connection.game_connection import GameConnection
from randovania.games.game import RandovaniaGame
from randovania.gui.generated.auto_tracker_window_ui import Ui_AutoTrackerWindow
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.game_connection_setup import GameConnectionSetup
from randovania.gui.widgets.item_tracker_widget import ItemTrackerWidget
from randovania.interface_common.options import Options


def load_trackers_configuration() -> dict[RandovaniaGame, dict[str, Path]]:
    with get_data_path().joinpath(f"gui_assets/tracker/trackers.json").open("r") as trackers_file:
        data = json.load(trackers_file)["trackers"]

    return {
        RandovaniaGame(game): {
            name: get_data_path().joinpath(f"gui_assets/tracker", file_name)
            for name, file_name in trackers.items()
        }
        for game, trackers in data.items()
    }


class AutoTrackerWindow(QtWidgets.QMainWindow, Ui_AutoTrackerWindow):
    trackers: dict[RandovaniaGame, dict[str, Path]]
    _full_name_to_path: dict[str, Path]
    _current_tracker_game: RandovaniaGame = None
    _current_tracker_name: str = None
    _item_tracker: ItemTrackerWidget

    def __init__(self, game_connection: GameConnection, options: Options):
        super().__init__()
        self.setupUi(self)
        self.game_connection = game_connection
        self.options = options
        common_qt_lib.set_default_window_icon(self)

        self.trackers = load_trackers_configuration()

        self._action_to_name = {}
        self._full_name_to_path = {}
        theme_group = QtGui.QActionGroup(self)

        for game in sorted(self.trackers.keys(), key=lambda k: k.long_name):
            game_menu = QtWidgets.QMenu(self.menu_tracker)
            game_menu.setTitle(game.long_name)
            self.menu_tracker.addMenu(game_menu)
            for name in sorted(self.trackers[game].keys()):
                action = QtGui.QAction(game_menu)
                action.setText(name)
                action.setCheckable(True)
                full_name = f"{game.long_name} - {name}"
                action.setChecked(full_name == options.selected_tracker)
                action.triggered.connect(self._on_action_select_tracker)
                game_menu.addAction(action)
                self._action_to_name[action] = full_name
                self._full_name_to_path[full_name] = self.trackers[game][name]
                theme_group.addAction(action)

        self.create_tracker()

        self.game_connection_setup = GameConnectionSetup(self, self.connection_status_label,
                                                         self.game_connection, options)
        self.game_connection_setup.create_backend_entries(self.menu_backend)
        self.game_connection_setup.create_upload_nintendont_action(self.menu_options)
        self.game_connection_setup.refresh_backend()

        self.action_force_update.triggered.connect(self.on_force_update_button)

        self._update_timer = QtCore.QTimer(self)
        self._update_timer.setInterval(100)
        self._update_timer.timeout.connect(self._on_timer_update)
        self._update_timer.setSingleShot(True)

    def showEvent(self, event: QtGui.QShowEvent):
        self._update_timer.start()
        super().showEvent(event)

    def hideEvent(self, event: QtGui.QHideEvent):
        self._update_timer.stop()
        super().hideEvent(event)

    @property
    def selected_tracker(self) -> str | None:
        for action, name in self._action_to_name.items():
            if action.isChecked():
                return name

    def _on_action_select_tracker(self):
        with self.options as options:
            options.selected_tracker = self.selected_tracker
        self.create_tracker()

    @asyncSlot()
    async def _on_timer_update(self):
        await self._on_timer_update_raw()

    async def _on_timer_update_raw(self):
        try:
            current_status = self.game_connection.current_status
            if current_status not in {GameConnectionStatus.Disconnected, GameConnectionStatus.UnknownGame,
                                      GameConnectionStatus.WrongGame}:
                self.action_force_update.setEnabled(True)
            else:
                self.action_force_update.setEnabled(False)

            if current_status == GameConnectionStatus.InGame or current_status == GameConnectionStatus.TrackerOnly:
                if self.game_connection.connector.game_enum == self._current_tracker_game:
                    inventory = self.game_connection.get_current_inventory()
                    self.item_tracker.update_state(inventory)
                    self.game_connection_setup.on_game_connection_updated()
                else:
                    self.connection_status_label.setText("{}: Wrong Game ({})".format(
                        self.game_connection.backend_choice.pretty_text,
                        self.game_connection.current_game_name,
                    ))
        finally:
            self._update_timer.start()

    def delete_tracker(self):
        self.item_tracker.deleteLater()
        self.item_tracker = None

    def create_tracker(self):
        tracker_name = self.selected_tracker
        if tracker_name == self._current_tracker_name or tracker_name is None:
            return

        self.delete_tracker()

        with self._full_name_to_path[tracker_name].open("r") as tracker_details_file:
            tracker_details = json.load(tracker_details_file)

        game_enum = RandovaniaGame(tracker_details["game"])
        self.item_tracker = ItemTrackerWidget(tracker_details)
        self.gridLayout.addWidget(self.item_tracker, 0, 0, 1, 1)

        self._current_tracker_game = game_enum
        self.item_tracker.update_state({})

        self._current_tracker_name = tracker_name

    @asyncSlot()
    async def on_force_update_button(self):
        await self.game_connection.update_current_inventory()
        inventory = self.game_connection.get_current_inventory()
        logging.info("Inventory:" + "\n".join(
            f"{item.long_name}: {inv_item.amount}/{inv_item.capacity}"
            for item, inv_item in sorted(inventory.items(), key=lambda it: it[0].long_name)
        ))
