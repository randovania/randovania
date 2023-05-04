import pytest

from randovania.game_connection.connector.debug_remote_connector import DebugRemoteConnector
from randovania.games.game import RandovaniaGame
from randovania.gui.debug_backend_window import DebugConnectorWindow


@pytest.fixture(name="window")
def debug_connector_window(skip_qtbot) -> DebugConnectorWindow:
    window = DebugConnectorWindow(DebugRemoteConnector(RandovaniaGame.METROID_PRIME_ECHOES))
    skip_qtbot.addWidget(window.window)
    return window


def test_setup_locations_combo(window: DebugConnectorWindow):
    # Setup
    # Run
    window._setup_locations_combo()

    # Assert
    assert window.collect_location_combo.count() > 100
