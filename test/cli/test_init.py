from unittest.mock import MagicMock, patch

import pytest

from randovania import cli


@patch("randovania.cli.games", autospec=True)
@patch("randovania.cli.qt.create_subparsers", autospec=True)
def test_create_subparsers(mock_qt_create_subparsers: MagicMock,
                           mock_games: MagicMock,
                           ):
    # Setup
    root_parser = MagicMock()
    games = [MagicMock(), MagicMock()]
    mock_games.__iter__.return_value = games

    # Run
    cli.create_subparsers(root_parser)

    # Assert
    for game in games:
        game.create_subparsers.assert_called_once_with(root_parser)
    mock_qt_create_subparsers.assert_called_once_with(root_parser)


@pytest.mark.parametrize("args", [
    [],
    ["--version"],
])
@patch("argparse.ArgumentParser.exit", autospec=True)
def test_parse_args_valid(mock_exit: MagicMock,
                          args):
    # Run
    cli._create_parser().parse_args(args)

    # Assert
    mock_exit.assert_not_called()


@pytest.mark.parametrize("args", [
    ["-h"],
])
@patch("argparse.ArgumentParser.exit", autospec=True)
def test_parse_args_invvalid(mock_exit: MagicMock,
                             args):
    # Run
    parser = cli._create_parser()
    parser.parse_args(args)

    # Assert
    mock_exit.assert_called_once_with(parser)


@patch("randovania.cli.qt.run", autospec=True)
def test_run_args_no_option(mock_qt_run: MagicMock,
                            ):
    # Setup
    args = MagicMock()
    args.func = None

    # Run
    cli._run_args(args)

    # Assert
    mock_qt_run.assert_called_once_with(args)


def test_run_args_with_func():
    # Setup
    args = MagicMock()

    # Run
    cli._run_args(args)

    # Assert
    args.func.assert_called_once_with(args)


@patch("randovania.cli._run_args", autospec=True)
@patch("randovania.cli._create_parser", autospec=True)
def test_run_cli(mock_create_parser: MagicMock,
                 mock_run_args: MagicMock,
                 ):
    # Run
    cli.run_cli()

    # Assert
    mock_run_args.assert_called_once_with(mock_create_parser.return_value.parse_args.return_value)
