import subprocess
from unittest.mock import patch, MagicMock, call

import pytest

from randovania.games.prime import claris_randomizer


@patch("subprocess.Popen", autospec=True)
def test_run_with_args_success(mock_popen: MagicMock,
                               ):
    # Setup
    args = [MagicMock(), MagicMock()]
    finish_string = "We are done!"
    status_update = MagicMock()
    process = mock_popen.return_value.__enter__.return_value
    process.stdout = [
        " line 1",
        "line 2 ",
        "   ",
        finish_string,
        " post line "
    ]

    # Run
    claris_randomizer._run_with_args(args, finish_string, status_update)

    # Assert
    mock_popen.assert_called_once_with(
        [str(x) for x in args],
        stdout=subprocess.PIPE, bufsize=0, universal_newlines=True
    )
    status_update.assert_has_calls([
        call("line 1"),
        call("line 2"),
        call(finish_string),
    ])
    process.kill.assert_not_called()


@patch("subprocess.Popen", autospec=True)
def test_run_with_args_failure(mock_popen: MagicMock,
                               ):
    # Setup
    class CustomException(Exception):
        @classmethod
        def do_raise(cls, x):
            raise CustomException("test exception")

    finish_string = "We are done!"
    process = mock_popen.return_value.__enter__.return_value
    process.stdout = [" line 1"]

    # Run
    with pytest.raises(CustomException):
        claris_randomizer._run_with_args([], finish_string, CustomException.do_raise)

    # Assert
    mock_popen.assert_called_once_with([], stdout=subprocess.PIPE, bufsize=0, universal_newlines=True)
    process.kill.assert_called_once_with()
