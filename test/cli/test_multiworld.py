import argparse
from unittest.mock import MagicMock

import pytest

from randovania.cli import server


def test_server_command_logic(mocker):
    # Setup
    mock_create_app: MagicMock = mocker.patch("randovania.server.app.create_app")

    # Run
    server.flask_command_logic(None)

    # Assert
    mock_create_app.assert_called_once_with()
    mock_create_app.return_value.sio.sio.run(mock_create_app.return_value, host="0.0.0.0")


def test_create_subparsers():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    server.create_subparsers(subparsers)

    with pytest.raises(SystemExit):
        args = parser.parse_args(["multiworld"])
        args.func(args)
