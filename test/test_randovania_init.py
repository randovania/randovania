from pathlib import Path

import pytest

import randovania


@pytest.mark.parametrize("missing", [False, True])
def test_get_configuration_default(tmpdir, missing):
    # Setup
    randovania.CONFIGURATION_FILE_PATH = None if missing else Path(tmpdir).joinpath("configuration.json")

    # Run
    config = randovania.get_configuration()

    # Assert
    assert config == {
        "server_address": "http://127.0.0.1:5000",
        "socketio_path": "/socket.io",
    }


def test_get_configuration_file(tmpdir):
    # Setup
    Path(tmpdir).joinpath("configuration.json").write_text('{"foo": 5}')
    randovania.CONFIGURATION_FILE_PATH = Path(tmpdir).joinpath("configuration.json")

    # Run
    config = randovania.get_configuration()

    # Assert
    assert config == {
        "foo": 5,
    }
