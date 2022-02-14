from unittest.mock import MagicMock, patch, ANY

import pytest

from randovania import cli


def test_create_subparsers(mocker):
    # Setup
    mock_layout_create_subparsers = mocker.patch("randovania.cli.layout.create_subparsers")
    mock_gui_create_subparsers = mocker.patch("randovania.cli.gui.create_subparsers")

    root_parser = MagicMock()

    # Run
    cli.create_subparsers(root_parser)

    # Assert
    mock_layout_create_subparsers.assert_called_once_with(root_parser)
    mock_gui_create_subparsers.assert_called_once_with(root_parser)


@pytest.mark.parametrize("args", [
    [],
    ["--version"],
])
def test_parse_args_valid(args):
    # Run
    try:
        cli._create_parser().parse_args(args)

    except SystemExit as value:
        assert value is None


@pytest.mark.parametrize("args", [
    ["-h"],
])
def test_parse_args_invalid(args):
    # Run
    parser = cli._create_parser()

    with pytest.raises(SystemExit, match="^0$"):
        parser.parse_args(args)


def test_run_args_with_func():
    # Setup
    args = MagicMock()

    # Run
    cli._run_args(MagicMock(), args)

    # Assert
    args.func.assert_called_once_with(args)


def test_run_args_without_func():
    # Setup
    parser = MagicMock()
    args = MagicMock()
    args.func = None

    # Run
    with pytest.raises(SystemExit, match="^1$"):
        cli._run_args(parser, args)

    # Assert
    parser.print_help.assert_called_once_with()


@patch("randovania.cli._run_args", autospec=True)
@patch("randovania.cli._create_parser", autospec=True)
def test_run_cli(mock_create_parser: MagicMock,
                 mock_run_args: MagicMock,
                 ):
    # Setup
    argv = [MagicMock(), MagicMock(), MagicMock()]
    mock_run_args.return_value = 1234

    # Run
    with pytest.raises(SystemExit) as p:
        cli.run_cli(argv)

    # Assert
    mock_create_parser.return_value.parse_args.assert_called_once_with(argv[1:])
    mock_run_args.assert_called_once_with(mock_create_parser.return_value,
                                          mock_create_parser.return_value.parse_args.return_value)
    assert p.value.code == 1234


def test_run_pytest(mocker):
    mock_exit = mocker.patch("sys.exit")
    mock_main = mocker.patch("pytest.main")

    # Run
    cli.run_pytest(["a", "b", "c", "d"])

    # Assert
    mock_main.assert_called_once_with(["c", "d"], plugins=ANY)
    mock_exit.assert_called_once_with(mock_main.return_value)
