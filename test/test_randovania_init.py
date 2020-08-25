from pathlib import Path
from unittest.mock import patch

import randovania


@patch("randovania.get_data_path", autospec=True)
def test_get_configuration_default(mock_get_data_path, tmpdir):
    # Setup
    mock_get_data_path.return_value = Path(tmpdir)

    # Run
    config = randovania.get_configuration()

    # Assert
    assert config == {
        "server_address": "http://127.0.0.1:5000",
        "socketio_path": "/socket.io",
    }


@patch("randovania.get_data_path", autospec=True)
def test_get_configuration_file(mock_get_data_path, tmpdir):
    # Setup
    mock_get_data_path.return_value = Path(tmpdir)
    Path(tmpdir).joinpath("configuration.json").write_text('{"foo": 5}')

    # Run
    config = randovania.get_configuration()

    # Assert
    assert config == {
        "foo": 5,
    }
