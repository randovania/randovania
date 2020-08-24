from unittest.mock import MagicMock

from randovania.server import game_session


def test_setup_app():
    game_session.setup_app(MagicMock())
