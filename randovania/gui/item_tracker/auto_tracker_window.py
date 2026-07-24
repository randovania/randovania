from __future__ import annotations

import collections
import functools
import typing
from typing import TYPE_CHECKING

from PySide6 import QtGui, QtWidgets

from randovania import get_data_path
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.resources.inventory import Inventory
from randovania.gui.generated.auto_tracker_window_ui import Ui_AutoTrackerWindow
from randovania.gui.item_tracker.item_tracker_widget import ItemTrackerWidget
from randovania.gui.item_tracker.tracker_assets import TrackerCatalog
from randovania.gui.item_tracker.tracker_structure import TrackerStructure
from randovania.gui.lib import common_qt_lib
from randovania.interface_common import persistence
from randovania.lib import json_lib
from randovania.network_common.game_connection_status import GameConnectionStatus

if TYPE_CHECKING:
    from randovania.game_connection.builder.connector_builder import ConnectorBuilder
    from randovania.game_connection.connector.remote_connector import RemoteConnector
    from randovania.game_connection.game_connection import ConnectedGameState, GameConnection
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.options import Options


def load_trackers_configuration(for_solo: bool) -> dict[RandovaniaGame, TrackerCatalog]:
    included_folder = get_data_path().joinpath("gui_assets/tracker")
    user_folder = persistence.local_data_dir().joinpath("tracker/layout")

    folders = [included_folder]
    if user_folder.joinpath("trackers.json").is_file():
        folders.append(user_folder)

    layouts: dict[RandovaniaGame, dict[str, typing.Any]] = collections.defaultdict(dict)
    themes: dict[RandovaniaGame, dict[str, dict[str, typing.Any]]] = collections.defaultdict(dict)

    for folder in folders:
        trackers_config = json_lib.read_dict(folder.joinpath("trackers.json"))

        exclude_themes: dict[str, list[str]]
        if for_solo:
            exclude_themes = {}
        else:
            exclude_themes = typing.cast("dict", trackers_config["solo_only"])

        all_trackers: dict[str, dict[str, typing.Any]] = typing.cast("dict", trackers_config["trackers"])
        for game_value, game_config in all_trackers.items():
            game = RandovaniaGame(game_value)

            for layout_name, filename in game_config["layouts"].items():
                layouts[game][layout_name] = folder.joinpath(filename)

            for theme_name, per_layout in game_config["themes"].items():
                if theme_name in exclude_themes.get(game_value, []):
                    continue

                theme_paths = themes[game].setdefault(theme_name, {})
                for layout_name, filename in per_layout.items():
                    theme_paths[layout_name] = folder.joinpath(filename)

    return {
        game: TrackerCatalog(layouts=game_layouts, themes=themes.get(game, {}))
        for game, game_layouts in layouts.items()
    }


class AutoTrackerWindow(QtWidgets.QMainWindow, Ui_AutoTrackerWindow):
    trackers: dict[RandovaniaGame, TrackerCatalog]
    _layout_actions: dict[RandovaniaGame, list[QtGui.QAction]]
    _theme_actions: dict[RandovaniaGame, list[QtGui.QAction]]
    _connected_game: RandovaniaGame | None = None
    _current_tracker_game: RandovaniaGame | None = None
    _current_tracker_layout: str | None = None
    _current_tracker_theme: str | None = None
    _current_tracker_details: TrackerStructure | None = None
    item_tracker: ItemTrackerWidget | None = None
    _dummy_tracker: QtWidgets.QLabel | None = None
    _last_source: RemoteConnector | None = None
    _last_selected_builder: ConnectorBuilder | None = None
    _has_any_tracker: bool = False

    def __init__(self, game_connection: GameConnection, window_manager: WindowManager | None, options: Options) -> None:
        super().__init__()
        self.setupUi(self)
        self.game_connection = game_connection
        self.options = options
        common_qt_lib.set_default_window_icon(self)

        self.trackers = load_trackers_configuration(for_solo=True)
        self._layout_actions = collections.defaultdict(list)
        self._theme_actions = collections.defaultdict(list)
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

            catalog = self.trackers[game]

            layout_menu = game_menu.addMenu("Layout")
            layout_group = QtGui.QActionGroup(layout_menu)
            for layout_name in sorted(catalog.layouts.keys()):
                action = QtGui.QAction(layout_menu)
                action.setText(layout_name)
                action.setCheckable(True)
                action.setChecked(layout_name == options.selected_tracker_layout_for(game))
                action.triggered.connect(functools.partial(self._on_action_select_tracker_layout, game, layout_name))
                layout_group.addAction(action)
                layout_menu.addAction(action)
                self._layout_actions[game].append(action)

            theme_menu = game_menu.addMenu("Theme")
            theme_group = QtGui.QActionGroup(theme_menu)
            for theme_name in sorted(catalog.themes.keys()):
                action = QtGui.QAction(theme_menu)
                action.setText(theme_name)
                action.setCheckable(True)
                action.setChecked(theme_name == options.selected_tracker_theme_for(game))
                action.triggered.connect(functools.partial(self._on_action_select_tracker_theme, game, theme_name))
                theme_group.addAction(action)
                theme_menu.addAction(action)
                self._theme_actions[game].append(action)

        if window_manager is None:
            self.select_game_button.setVisible(False)
        else:
            self.select_game_button.clicked.connect(window_manager.open_game_connection_window)
        self.select_game_combo.currentIndexChanged.connect(self.on_select_game_combo)
        self.game_connection.BuildersChanged.connect(self.update_sources_combo)
        self.game_connection.GameStateUpdated.connect(self.on_game_state_updated)
        self.update_sources_combo()

    def selected_layout_for(self, game: RandovaniaGame) -> str | None:
        return self._first_checked_action_text(self._layout_actions[game])

    def selected_theme_for(self, game: RandovaniaGame) -> str | None:
        return self._first_checked_action_text(self._theme_actions[game])

    @staticmethod
    def _first_checked_action_text(actions: list[QtGui.QAction]) -> str | None:
        checked = [action for action in actions if action.isChecked()]
        if not checked:
            checked = actions

        if checked:
            return checked[0].text()

        return None

    def _check_theme_action(self, game: RandovaniaGame, name: str) -> None:
        for action in self._theme_actions[game]:
            action.setChecked(action.text() == name)
        with self.options as options:
            options.set_selected_tracker_theme_for(game, name)

    def _on_action_default_game(self, game: RandovaniaGame | None) -> None:
        with self.options as options:
            options.tracker_default_game = game

        self.create_tracker()

    def _on_action_select_tracker_layout(self, game: RandovaniaGame, name: str) -> None:
        with self.options as options:
            options.set_selected_tracker_layout_for(game, name)
        self.create_tracker()

    def _on_action_select_tracker_theme(self, game: RandovaniaGame, name: str) -> None:
        with self.options as options:
            options.set_selected_tracker_theme_for(game, name)
        self.create_tracker()

    def delete_tracker(self) -> None:
        if self.item_tracker is not None:
            self.item_tracker.deleteLater()
            self.item_tracker = None

        if self._dummy_tracker is not None:
            self._dummy_tracker.deleteLater()
            self._dummy_tracker = None

    def get_connector(self) -> RemoteConnector | None:
        builder = self.selected_builder()
        return self.game_connection.get_connector_for_builder(builder)

    def create_tracker(self) -> None:
        connector = self.get_connector()
        layout_name: str | None = None
        theme_name: str | None = None
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

        if target_game is None:
            target_game = self.options.tracker_default_game

        if target_game is not None:
            layout_name = self.selected_layout_for(target_game)
            theme_name = self.selected_theme_for(target_game)

            if layout_name is not None and theme_name is not None:
                catalog = self.trackers[target_game]
                if theme_name not in catalog.theme_names_for(layout_name):
                    # The previously selected theme doesn't exist for this layout (e.g. a
                    # "Stream-friendly" theme that's only defined for one specific layout).
                    # Fall back to any theme that does cover it.
                    available = catalog.theme_names_for(layout_name)
                    theme_name = available[0] if available else None
                    if theme_name is not None:
                        self._check_theme_action(target_game, theme_name)

        if (
            self._has_any_tracker
            and layout_name == self._current_tracker_layout
            and theme_name == self._current_tracker_theme
            and target_game == self._current_tracker_game
        ):
            return

        self.delete_tracker()

        if target_game is None or layout_name is None or theme_name is None:
            if target_game is None:
                msg = "Not currently connected to any games"
            else:
                msg = f"{target_game.long_name} does not support auto tracking"

            self._dummy_tracker = QtWidgets.QLabel(msg, self)
            self._dummy_tracker.setWordWrap(True)
            self.gridLayout.addWidget(self._dummy_tracker, 0, 0, 1, 1)
            tracker_details = None
        else:
            paths = self.trackers[target_game].resolve(layout_name, theme_name)
            tracker_details, tracker_theme = paths.load()

            self.item_tracker = ItemTrackerWidget(tracker_details, tracker_theme)
            self.gridLayout.addWidget(self.item_tracker, 0, 0, 1, 1)
            self.item_tracker.update_state(inventory)

        self._has_any_tracker = True
        self._current_tracker_game = target_game
        self._current_tracker_layout = layout_name
        self._current_tracker_theme = theme_name
        self._current_tracker_details = tracker_details
        if connector is not None:
            connector.inform_connected_tracker(tracker_details)

    def update_sources_combo(self) -> None:
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

    def on_select_game_combo(self, index: int) -> None:
        builder = self.selected_builder()
        if builder != self._last_selected_builder:
            self.delete_tracker()
            self._current_tracker_game = None
            self.create_tracker()
        self._last_selected_builder = builder

    def on_game_state_updated(self, state: ConnectedGameState) -> None:
        self.create_tracker()
        expected_connector = self.get_connector()
        if expected_connector == state.source or self._last_source == state.source:
            if state.status == GameConnectionStatus.Disconnected:
                self._last_source = None
                return

            if self._last_source != state.source:
                state.source.inform_connected_tracker(self._current_tracker_details)

            self._last_source = state.source
            if self.item_tracker is not None:
                self.item_tracker.update_state(state.current_inventory)
