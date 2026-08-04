from __future__ import annotations

import typing
import uuid
from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_connection.builder.debug_connector_builder import DebugConnectorBuilder
from randovania.game_connection.builder.dolphin_connector_builder import DolphinConnectorBuilder
from randovania.game_connection.game_connection import ConnectedGameState
from randovania.gui.item_tracker.auto_tracker_window import AutoTrackerWindow
from randovania.gui.item_tracker.item_tracker_widget import ItemTrackerWidget
from randovania.gui.item_tracker.tracker_assets import ThemeSource, TrackerAssetPaths, TrackerCatalog
from randovania.lib import json_lib
from randovania.network_common.game_connection_status import GameConnectionStatus


def test_create_tracker_no_game(skip_qtbot):
    # Setup
    options = MagicMock()
    options.tracker_default_game = None

    connection = MagicMock()
    connection.connected_states = {}
    connection.get_connector_for_builder.return_value = None

    connector = MagicMock()
    connector.game_enum = RandovaniaGame.METROID_PRIME

    # Run
    window = AutoTrackerWindow(connection, None, options)
    skip_qtbot.addWidget(window)
    # window.create_tracker() is implied

    # Assert
    assert window.item_tracker is None
    assert window._dummy_tracker is not None

    # Now swap to a proper tracker
    connection.get_connector_for_builder.return_value = connector
    window.create_tracker()

    assert window._dummy_tracker is None
    assert window._current_tracker_game == RandovaniaGame.METROID_PRIME


@pytest.mark.parametrize(
    "game",
    [RandovaniaGame.METROID_PRIME, RandovaniaGame.METROID_PRIME_ECHOES],
)
def test_create_tracker_valid(skip_qtbot, game):
    # Setup
    connection = MagicMock()
    connector = connection.get_connector_for_builder.return_value
    connector.game_enum = game
    connection.connected_states = {
        connector: ConnectedGameState(uuid.UUID(int=0), connector, GameConnectionStatus.Disconnected)
    }

    # Run
    window = AutoTrackerWindow(connection, None, MagicMock())
    skip_qtbot.addWidget(window)
    # window.create_tracker() is implied

    # Assert
    assert isinstance(window.item_tracker, ItemTrackerWidget)
    assert len(window.item_tracker.tracker_elements) > 10
    assert window._dummy_tracker is None
    assert window._current_tracker_game == game

    # Layout and theme can be selected independently
    layout_action = next(action for action in window._layout_actions if action.text() == "8 Lines")
    layout_action.setChecked(True)
    window.create_tracker()
    assert window._current_tracker_layout == "8 Lines"

    theme_action = next(action for action in window._theme_actions if action.text() == "Pixel Art")
    theme_action.setChecked(True)
    window.create_tracker()
    assert window._current_tracker_theme == "Pixel Art"
    assert window._current_tracker_layout == "8 Lines"


def test_create_tracker_shows_error_for_broken_theme(skip_qtbot, mocker):
    # Setup
    game = RandovaniaGame.METROID_PRIME
    connection = MagicMock()
    connector = connection.get_connector_for_builder.return_value
    connector.game_enum = game
    connection.connected_states = {
        connector: ConnectedGameState(uuid.UUID(int=0), connector, GameConnectionStatus.Disconnected)
    }

    # Run
    window = AutoTrackerWindow(connection, None, MagicMock())
    skip_qtbot.addWidget(window)
    assert isinstance(window.item_tracker, ItemTrackerWidget)

    mocker.patch.object(TrackerAssetPaths, "load", side_effect=ValueError("Theme is missing an image named 'Foo'"))
    window._current_tracker_layout = None  # force create_tracker() past the no-op "already showing this" check
    window.create_tracker()

    # Assert
    assert window.item_tracker is None
    assert window._dummy_tracker is not None
    assert "Foo" in window._dummy_tracker.text()


def test_fall_back_to_default_game(skip_qtbot):
    # Setup
    # default game = Prime
    options = MagicMock()
    options.tracker_default_game = RandovaniaGame.METROID_PRIME
    options.selected_tracker_layout_for.return_value = "Standard"

    # connected game = Echoes
    connector = MagicMock()
    connector.game_enum = RandovaniaGame.METROID_PRIME_ECHOES
    connected_builder = DolphinConnectorBuilder()

    # random builder with no connection
    disconnected_builder = DebugConnectorBuilder(RandovaniaGame.BLANK.value)

    connection = MagicMock()
    connection.connection_builders = [disconnected_builder, connected_builder]
    connection.connected_states = {
        connector: ConnectedGameState(uuid.UUID(int=0), connector, GameConnectionStatus.InGame)
    }
    connection.get_connector_for_builder.side_effect = lambda builder: (
        connector if builder is connected_builder else None
    )

    # Run
    window = AutoTrackerWindow(connection, None, options)
    skip_qtbot.addWidget(window)

    # select a connected game shows the tracker for the game
    window.select_game_combo.setCurrentIndex(window.select_game_combo.findData(connected_builder))
    assert window._current_tracker_game == RandovaniaGame.METROID_PRIME_ECHOES
    assert isinstance(window.item_tracker, ItemTrackerWidget)

    # select a not-connected source and it should show the default game
    window.select_game_combo.setCurrentIndex(window.select_game_combo.findData(disconnected_builder))
    assert window._current_tracker_game == RandovaniaGame.METROID_PRIME
    assert isinstance(window.item_tracker, ItemTrackerWidget)
    assert window._dummy_tracker is None
    assert window.connected_game_state_label.text() == "Not Connected"


def test_on_disconnect_goes_back_to_default(skip_qtbot):
    # Setup
    connection = MagicMock()
    connector = MagicMock()
    connection.get_connector_for_builder.return_value = None
    options = MagicMock()
    options.tracker_default_game = RandovaniaGame.BLANK

    window = AutoTrackerWindow(connection, None, options)
    skip_qtbot.addWidget(window)
    window.create_tracker = MagicMock()
    window.selected_builder = MagicMock()
    window._update_theme_and_layout_menus = MagicMock()
    window._last_source = connector

    # Run
    window.on_game_state_updated(
        ConnectedGameState(uuid.UUID(int=0), connector, status=GameConnectionStatus.Disconnected)
    )

    # Assert
    window.create_tracker.assert_called_once_with()
    assert window._last_source is None


def test_update_sources_combo(skip_qtbot):
    # Setup
    options = MagicMock()
    options.tracker_default_game = None

    connection = MagicMock()
    connection.connected_states = {}
    connection.get_connector_for_builder.return_value = None
    connection.connection_builders = []

    # Run
    window = AutoTrackerWindow(connection, None, options)
    skip_qtbot.addWidget(window)

    # Empty
    # window.update_sources_combo() is implied
    assert window.select_game_combo.itemText(0) == "No sources available"
    assert window.select_game_combo.count() == 1

    # One builder
    builder = DolphinConnectorBuilder()
    connection.connection_builders = [builder]
    window.update_sources_combo()
    assert window.select_game_combo.itemText(0) == "Dolphin"
    assert window.select_game_combo.count() == 1

    # Two builders
    builder2 = DebugConnectorBuilder(RandovaniaGame.BLANK.value)
    connection.connection_builders = [builder2, builder]
    window.update_sources_combo()
    assert window.select_game_combo.itemText(0) == "Debug"
    assert window.select_game_combo.itemText(1) == "Dolphin"
    assert window.select_game_combo.currentIndex() == 1
    assert window.select_game_combo.count() == 2


@pytest.mark.parametrize("correct_source", [False, True])
def test_on_game_state_updated(skip_qtbot, correct_source):
    # Setup
    inventory = MagicMock()
    connection = MagicMock()
    connector = MagicMock()
    # Return None during __init__ so create_tracker() exits early without crashing
    connection.get_connector_for_builder.return_value = None
    options = MagicMock()
    options.tracker_default_game = RandovaniaGame.BLANK

    # Run
    window = AutoTrackerWindow(connection, None, options)
    # Now set up the real connector and reset call history from init
    connection.get_connector_for_builder.return_value = connector
    connection.get_connector_for_builder.reset_mock()
    window.create_tracker = MagicMock()
    window.selected_builder = MagicMock()
    window.item_tracker = MagicMock()
    skip_qtbot.addWidget(window)
    window.on_game_state_updated(
        ConnectedGameState(
            uuid.UUID(int=0),
            connector if correct_source else MagicMock(),
            status=GameConnectionStatus.TitleScreen,
            current_inventory=inventory,
        )
    )

    # Assert
    connection.get_connector_for_builder.assert_called_once_with(window.selected_builder.return_value)
    if correct_source:
        window.item_tracker.update_state.assert_called_once_with(inventory)
    else:
        window.item_tracker.update_state.assert_not_called()


def _bundled_tracker_catalogs() -> Iterator[tuple[RandovaniaGame, TrackerCatalog]]:
    """Every game's own bundled tracker data, ignoring any local user override.

    A user's local override only needs to be internally consistent with itself (see
    test_tracker_data_integrity.py, which validates it the same way) - it isn't required to
    also cover every layout Randovania ships, so it's excluded here to keep this check
    hermetic and independent of whatever happens to exist on the machine running it.
    """
    for game in RandovaniaGame.all_games():
        game_dir = game.data_path.joinpath("assets", "tracker")
        trackers_json = game_dir.joinpath("trackers.json")
        if not trackers_json.is_file():
            continue

        game_config = typing.cast("dict[str, dict[str, str]]", json_lib.read_dict(trackers_json))
        layouts = {name: game_dir.joinpath(filename) for name, filename in game_config["layouts"].items()}
        themes = {
            name: ThemeSource(path=game_dir.joinpath(filename), assets_root=game_dir)
            for name, filename in game_config["themes"].items()
        }
        yield game, TrackerCatalog(layouts=layouts, themes=themes)


def _get_tracker_combos() -> Iterator[tuple[RandovaniaGame, str, str, TrackerCatalog]]:
    for game, catalog in _bundled_tracker_catalogs():
        for layout_name in catalog.layouts:
            for theme_name in catalog.themes:
                yield game, layout_name, theme_name, catalog


@pytest.mark.parametrize(("game", "layout_name", "theme_name", "catalog"), list(_get_tracker_combos()))
def test_validate_tracker_json(game: RandovaniaGame, layout_name: str, theme_name: str, catalog: TrackerCatalog):
    catalog.resolve(layout_name, theme_name).load()
