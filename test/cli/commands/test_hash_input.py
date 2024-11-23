import argparse
from pathlib import Path

import pytest_mock

from randovania.cli.commands import hash_input


def test_hash_input_logic_file(tmp_path: Path, mocker: pytest_mock.MockFixture) -> None:
    args = argparse.Namespace()
    args.input_path = tmp_path.joinpath("input")
    tmp_path.joinpath("input").write_bytes(b"foo")

    mock_print = mocker.patch("randovania.cli.commands.hash_input.print")

    # Run
    hash_input.hash_input_command_logic(args)

    # Assert
    mock_print.assert_called_once_with("sha1:0beec7b5ea3f0fdbc95d0dd47f3c5bc275da8a33")


def test_hash_input_logic_dir(tmp_path: Path, mocker: pytest_mock.MockFixture) -> None:
    args = argparse.Namespace()
    args.input_path = tmp_path.joinpath("input")
    tmp_path.joinpath("input").mkdir()
    tmp_path.joinpath("input", "a").write_bytes(b"foo")

    mock_print = mocker.patch("randovania.cli.commands.hash_input.print")

    # Run
    hash_input.hash_input_command_logic(args)

    # Assert
    mock_print.assert_called_once_with("sha1:f3a2a51a9b0f2be2468926b4132313728c250dbf")
