from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

import pytest

from randovania.cli import server

if TYPE_CHECKING:
    import pytest_mock


def test_server_command_logic(mocker: pytest_mock.MockerFixture):
    # Setup
    mock_configuration = mocker.patch("randovania.get_configuration")
    mock_create_app = mocker.patch("randovania.server.app.create_app")
    mock_monitoring_init = mocker.patch("randovania.monitoring.server_init")

    # Run
    server.flask_command_logic(None)

    # Assert
    mock_configuration.return_value.get.assert_called_once_with("sentry_sampling_rate", 1.0)
    mock_create_app.assert_called_once_with()
    mock_monitoring_init.assert_called_once_with(sampling_rate=mock_configuration.return_value.get.return_value)
    mock_create_app.return_value.sio.sio.run(mock_create_app.return_value, host="0.0.0.0")


def test_create_subparsers():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    server.create_subparsers(subparsers)

    with pytest.raises(SystemExit):
        parser.parse_args(["multiworld"])
