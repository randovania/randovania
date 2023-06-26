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
    sio = MagicMock()

    # Run
    multiplayer.setup_app(sio)

    # Assert
    for mock in mocks:
        mock.assert_called_once_with(sio)
