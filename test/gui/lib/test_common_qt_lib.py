from unittest.mock import MagicMock

from randovania.gui.lib import common_qt_lib


def test_get_network_client(skip_qtbot, qapp):
    qapp.network_client = MagicMock()

    assert common_qt_lib.get_network_client() is qapp.network_client


def test_get_game_connection(skip_qtbot, qapp):
    qapp.game_connection = MagicMock()

    assert common_qt_lib.get_game_connection() is qapp.game_connection
