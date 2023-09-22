from __future__ import annotations

import pytest

from randovania.game_connection.connector.debug_remote_connector import DebugRemoteConnector
from randovania.games.game import RandovaniaGame
from randovania.gui.debug_backend_window import DebugConnectorWindow
from randovania.gui.lib import model_lib
from randovania.interface_common.players_configuration import INVALID_UUID


@pytest.fixture(name="window")
def debug_connector_window(skip_qtbot) -> DebugConnectorWindow:
    window = DebugConnectorWindow(DebugRemoteConnector(RandovaniaGame.METROID_PRIME_ECHOES, INVALID_UUID))
    skip_qtbot.addWidget(window.window)
    return window


def test_setup_locations_combo(window: DebugConnectorWindow):
    # Setup
    # Run
    window._setup_locations_combo()

    # Assert
    assert window.collect_location_combo.count() > 100


async def test_has_messages(window: DebugConnectorWindow):
    await window.connector.display_arbitrary_message("Hello World")

    assert model_lib.get_texts(window.messages_item_model) == ["Hello World"]


async def test_remote_pickups(window: DebugConnectorWindow, blank_pickup):
    await window.connector.set_remote_pickups((("The Source", blank_pickup),))
    assert model_lib.get_texts(window.messages_item_model) == ["Received Blank Pickup from The Source"]

    await window.connector.set_remote_pickups(
        (
            ("The Source", blank_pickup),
            ("Your Boss", blank_pickup),
        )
    )
    assert model_lib.get_texts(window.messages_item_model) == [
        "Received Blank Pickup from The Source",
        "Received Blank Pickup from Your Boss",
    ]
