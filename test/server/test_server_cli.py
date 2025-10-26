from __future__ import annotations

import argparse
from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock

import pytest
import uvicorn
import uvicorn.config

from randovania.cli import server

if TYPE_CHECKING:
    import pytest_mock


@pytest.mark.parametrize("mode", ["dev", "prod", "other"])
def test_server_command_logic(mocker: pytest_mock.MockerFixture, mode: str):
    # Setup
    mock_configuration = mocker.patch("randovania.get_configuration")
    mock_monitoring_init = mocker.patch("randovania.monitoring.server_init")
    mock_uvicorn_run = mocker.patch("uvicorn.run")
    mock_log = mocker.patch("logging.warning")

    mock_log_config = MagicMock()
    uvicorn.config.LOGGING_CONFIG = mock_log_config

    args = MagicMock()
    args.mode = mode

    # Run
    server.run_command_logic(args)

    # Assert
    mock_configuration.return_value.get.assert_called_once_with("sentry_sampling_rate", 1.0)
    mock_monitoring_init.assert_called_once_with(sampling_rate=mock_configuration.return_value.get.return_value)
    mock_uvicorn_run.assert_called_once_with(
        "randovania.server.app_module:app",
        host="0.0.0.0",
        port=5000,
        log_config=mock_log_config,
        reload=bool(mode == "dev"),
        reload_excludes=ANY,
        forwarded_allow_ips="*",
    )
    if mode == "other":
        mock_log.assert_called_once_with("Unknown server mode 'other'. Running in prod mode.")
    else:
        mock_log.assert_not_called()


def test_create_subparsers():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    server.create_subparsers(subparsers)

    with pytest.raises(SystemExit):
        parser.parse_args(["multiworld"])
