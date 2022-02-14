from pathlib import Path

import pytest

import randovania


def test_get_configuration_default_missing(tmpdir, mocker):
    # Setup
    randovania.CONFIGURATION_FILE_PATH = None
    mocker.patch("randovania._get_default_configuration_path", return_value=Path(tmpdir).joinpath("missing.json"))

    # Run
    config = randovania.get_configuration()

    # Assert
    assert config == {
        "server_address": "http://127.0.0.1:5000",
        "socketio_path": "/socket.io",
    }


@pytest.mark.parametrize("from_configured", [False, True])
def test_get_configuration_file(tmpdir, mocker, from_configured):
    # Setup
    mocker.patch("randovania._get_default_configuration_path", return_value=Path(tmpdir).joinpath("provided.json"))
    if from_configured:
        Path(tmpdir).joinpath("configuration.json").write_text('{"foo": 5}')
        randovania.CONFIGURATION_FILE_PATH = Path(tmpdir).joinpath("configuration.json")
    else:
        Path(tmpdir).joinpath("provided.json").write_text('{"foo": 5}')

    # Run
    config = randovania.get_configuration()

    # Assert
    assert config == {
        "foo": 5,
    }


def test_get_invalid_configuration_file(tmpdir):
    # Setup
    randovania.CONFIGURATION_FILE_PATH = Path(tmpdir).joinpath("configuration.json")

    # Run
    with pytest.raises(FileNotFoundError):
        randovania.get_configuration()
