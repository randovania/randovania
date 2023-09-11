from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from randovania.game_connection.builder.debug_connector_builder import DebugConnectorBuilder
from randovania.game_connection.builder.dolphin_connector_builder import DolphinConnectorBuilder
from randovania.game_connection.game_connection import ConnectedGameState
from randovania.games.game import RandovaniaGame
from randovania.gui.auto_tracker_window import AutoTrackerWindow
from randovania.gui.widgets.item_tracker_widget import ItemTrackerWidget
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
    ("game", "tracker_name"),
    [
        (RandovaniaGame.METROID_PRIME, "Game Art (Standard)"),
        (RandovaniaGame.METROID_PRIME_ECHOES, "Game Art (Standard)"),
    ],
)
def test_create_tracker_valid(skip_qtbot, game, tracker_name):
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

    # Select new theme
    action = [action for action in window._tracker_actions[game] if action.text() == tracker_name][0]
    action.setChecked(True)

    window.create_tracker()
    assert window._current_tracker_name == tracker_name


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
def test_on_game_state_updated(skip_qtbot, mocker, correct_source):
    # Setup
    inventory = MagicMock()
    connection = MagicMock()
    connector = connection.get_connector_for_builder.return_value
    mocker.patch("randovania.gui.auto_tracker_window.AutoTrackerWindow.create_tracker")

    # Run
    window = AutoTrackerWindow(connection, None, MagicMock())
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
