from unittest.mock import MagicMock

from randovania.server import user_session


def test_setup_app():
    user_session.setup_app(MagicMock(), MagicMock())
