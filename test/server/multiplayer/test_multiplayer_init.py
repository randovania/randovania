from __future__ import annotations

from unittest.mock import MagicMock

from randovania.server import multiplayer


def test_setup_app(mocker):
    mocks: list[MagicMock] = [
        mocker.patch(f"randovania.server.multiplayer.{name}.setup_app")
        for name in [
            "session_api",
            "session_admin",
            "web_api",
            "world_api",
        ]
    ]
    sa = MagicMock()

    # Run
    multiplayer.setup_app(sa)

    # Assert
    for mock in mocks:
        mock.assert_called_once_with(sa)
