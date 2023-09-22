from __future__ import annotations

import collections
import functools
from typing import TYPE_CHECKING

from PySide6 import QtGui, QtWidgets

from randovania import get_data_path
from randovania.game_description.resources.inventory import Inventory
from randovania.games.game import RandovaniaGame
from randovania.gui.generated.auto_tracker_window_ui import Ui_AutoTrackerWindow
from randovania.gui.lib import common_qt_lib
from randovania.gui.widgets.item_tracker_widget import ItemTrackerWidget
from randovania.lib import json_lib
from randovania.network_common.game_connection_status import GameConnectionStatus

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.game_connection.builder.connector_builder import ConnectorBuilder
    from randovania.game_connection.connector.remote_connector import RemoteConnector
    from randovania.game_connection.game_connection import ConnectedGameState, GameConnection
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.options import Options


def load_trackers_configuration(for_solo: bool) -> dict[RandovaniaGame, dict[str, Path]]:
    data = json_lib.read_path(get_data_path().joinpath("gui_assets/tracker/trackers.json"))

    if for_solo:
        exclude_trackers = {}
    else:
        exclude_trackers = data["solo_only"]

    return {
        RandovaniaGame(game): {
            name: get_data_path().joinpath("gui_assets/tracker", file_name)
            for name, file_name in trackers.items()
            if name not in exclude_trackers.get(game, [])
        }
        for game, trackers in data["trackers"].items()
    }


class AutoTrackerWindow(QtWidgets.QMainWindow, Ui_AutoTrackerWindow):
    trackers: dict[RandovaniaGame, dict[str, Path]]
    _tracker_actions: dict[RandovaniaGame, list[QtGui.QAction]]
    _full_name_to_path: dict[str, Path]
    _connected_game: RandovaniaGame | None = None
    _current_tracker_game: RandovaniaGame | None = None
    _current_tracker_name: str = "undefined"
    item_tracker: ItemTrackerWidget | None = None
    _dummy_tracker: QtWidgets.QLabel | None = None
    _last_source: RemoteConnector | None = None
    _last_selected_builder: ConnectorBuilder | None = None

    def __init__(self, game_connection: GameConnection, window_manager: WindowManager | None, options: Options):
        super().__init__()
        self.setupUi(self)
        self.game_connection = game_connection
        self.options = options
        common_qt_lib.set_default_window_icon(self)

        self.trackers = load_trackers_configuration(for_solo=True)
        self._tracker_actions = collections.defaultdict(list)
        self.connected_game_state_label.setText(GameConnectionStatus.Disconnected.pretty_text)

        self._current_tracker_game = options.tracker_default_game
        default_game_action_group = QtGui.QActionGroup(self.menu_default_game)
        default_game_action: QtGui.QAction = self.menu_default_game.addAction("None")
        default_game_action.setCheckable(True)
        default_game_action.setChecked(options.tracker_default_game is None)
        default_game_action.triggered.connect(functools.partial(self._on_action_default_game, None))
        default_game_action_group.addAction(default_game_action)

        for game in sorted(self.trackers.keys(), key=lambda k: k.long_name):
            default_game_action = self.menu_default_game.addAction(game.long_name)
            default_game_action.setCheckable(True)
            default_game_action.setChecked(options.tracker_default_game == game)
            default_game_action.triggered.connect(functools.partial(self._on_action_default_game, game))
            default_game_action_group.addAction(default_game_action)

            game_menu = QtWidgets.QMenu(self.menu_tracker)
            game_menu.setTitle(game.long_name)
            self.menu_tracker.addMenu(game_menu)

            group = QtGui.QActionGroup(game_menu)
            for name in sorted(self.trackers[game].keys()):
                action = QtGui.QAction(game_menu)
                action.setText(name)
                action.setCheckable(True)
                action.setChecked(name == options.selected_tracker_for(game))
                action.triggered.connect(functools.partial(self._on_action_select_tracker, game, name))
                group.addAction(action)
                game_menu.addAction(action)
                self._tracker_actions[game].append(action)

        if window_manager is None:
            self.select_game_button.setVisible(False)
        else:
            self.select_game_button.clicked.connect(window_manager.open_game_connection_window)
        self.select_game_combo.currentIndexChanged.connect(self.on_select_game_combo)
        self.game_connection.BuildersChanged.connect(self.update_sources_combo)
        self.game_connection.GameStateUpdated.connect(self.on_game_state_updated)
        self.update_sources_combo()

    def selected_tracker_for(self, game: RandovaniaGame) -> str | None:
        actions = [action for action in self._tracker_actions[game] if action.isChecked()]
        if not actions:
            actions = self._tracker_actions[game]

        if actions:
            return actions[0].text()

        return None

    def _on_action_default_game(self, game: RandovaniaGame):
        with self.options as options:
            options.tracker_default_game = game

        if self._last_source is None:
            self._current_tracker_game = game
            if game is None:
                self.delete_tracker()
            self.create_tracker()

    def _on_action_select_tracker(self, game: RandovaniaGame, name: str):
        with self.options as options:
            options.set_selected_tracker_for(game, name)
        self.create_tracker()

    def delete_tracker(self):
        if self.item_tracker is not None:
            self.item_tracker.deleteLater()
            self.item_tracker = None

        if self._dummy_tracker is not None:
            self._dummy_tracker.deleteLater()
            self._dummy_tracker = None

    def create_tracker(self):
        connector = self.game_connection.get_connector_for_builder(self.selected_builder())
        tracker_name: str | None = None
        target_game: RandovaniaGame | None = None

        inventory: Inventory = Inventory.empty()

        if self.item_tracker is not None:
            inventory = self.item_tracker.current_state

        if connector is not None:
            target_game = connector.game_enum

            state = self.game_connection.connected_states.get(connector)
            status = GameConnectionStatus.Disconnected
            if state is not None:
                inventory = state.current_inventory
                status = state.status

            self.connected_game_state_label.setText(f"{target_game.long_name}: {status.pretty_text}")
        else:
            self.connected_game_state_label.setText("Not Connected")

        if target_game is None and self._current_tracker_game is not None:
            target_game = self._current_tracker_game

        if target_game is not None:
            tracker_name = self.selected_tracker_for(target_game)

        if tracker_name == self._current_tracker_name and target_game == self._current_tracker_game:
            return

        self.delete_tracker()

        if target_game is None or tracker_name is None:
            if target_game is None:
                msg = "Not currently connected to any games"
            else:
                msg = f"{target_game.long_name} does not support auto tracking"

            self._dummy_tracker = QtWidgets.QLabel(msg, self)
            self._dummy_tracker.setWordWrap(True)
            self.gridLayout.addWidget(self._dummy_tracker, 0, 0, 1, 1)
        else:
            tracker_details = json_lib.read_path(self.trackers[target_game][tracker_name])

            self.item_tracker = ItemTrackerWidget(tracker_details)
            self.gridLayout.addWidget(self.item_tracker, 0, 0, 1, 1)
            self.item_tracker.update_state(inventory)

        self._current_tracker_game = target_game
        self._current_tracker_name = tracker_name

    def update_sources_combo(self):
        old_builder = self.selected_builder()
        self.select_game_combo.currentIndexChanged.disconnect(self.on_select_game_combo)
        self.select_game_combo.clear()

        index_to_select = None
        for i, builder in enumerate(self.game_connection.connection_builders):
            if builder == old_builder:
                index_to_select = i
            self.select_game_combo.addItem(
                builder.pretty_text,
                builder,
            )

        if not self.game_connection.connection_builders:
            self.select_game_combo.addItem("No sources available")

        if index_to_select is not None:
            self.select_game_combo.setCurrentIndex(index_to_select)
        self.select_game_combo.currentIndexChanged.connect(self.on_select_game_combo)

        self.create_tracker()

    def selected_builder(self) -> ConnectorBuilder | None:
        return self.select_game_combo.currentData()

    def on_select_game_combo(self, _):
        builder = self.selected_builder()
        if builder != self._last_selected_builder:
            self.delete_tracker()
            self._current_tracker_game = None
            self.create_tracker()
        self._last_selected_builder = builder

    def on_game_state_updated(self, state: ConnectedGameState):
        self.create_tracker()
        expected_connector = self.game_connection.get_connector_for_builder(self.selected_builder())
        if expected_connector == state.source or self._last_source == state.source:
            self._last_source = state.source
            if self.item_tracker is not None:
                self.item_tracker.update_state(state.current_inventory)
