import pytest

from randovania.games.common.dotnet import DotnetNotSetupException, is_dotnet_set_up


def test_dotnet_missing(mocker):
    mocker.patch("subprocess.run", side_effect=FileNotFoundError)

    with pytest.raises(DotnetNotSetupException):
        is_dotnet_set_up()


def test_dotnet_on_error(mocker):
    dotnet_process = mocker.patch("subprocess.run")
    dotnet_process.return_value.returncode = 1

    with pytest.raises(DotnetNotSetupException):
        is_dotnet_set_up()


def test_dotnet_runs_fine(mocker):
    dotnet_process = mocker.patch("subprocess.run")
    dotnet_process.return_value.returncode = 0

    is_dotnet_set_up()
