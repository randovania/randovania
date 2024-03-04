from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import randovania

if TYPE_CHECKING:
    from pathlib import Path

    import pytest_mock
    from _pytest.monkeypatch import MonkeyPatch


def test_get_configuration_default_missing(
    tmp_path: Path, mocker: pytest_mock.MockerFixture, monkeypatch: MonkeyPatch
) -> None:
    # Setup
    monkeypatch.setattr(randovania, "CONFIGURATION_FILE_PATH", None)
    mocker.patch("randovania._get_default_configuration_path", return_value=tmp_path.joinpath("missing.json"))

    # Run
    config = randovania.get_configuration()

    # Assert
    assert config == {
        "server_address": "http://127.0.0.1:5000",
        "socketio_path": "/socket.io",
    }


@pytest.mark.parametrize("from_configured", [False, True])
def test_get_configuration_file(
    tmp_path: Path, monkeypatch: MonkeyPatch, mocker: pytest_mock.MockerFixture, from_configured: bool
) -> None:
    # Setup
    mocker.patch("randovania._get_default_configuration_path", return_value=tmp_path.joinpath("provided.json"))
    if from_configured:
        tmp_path.joinpath("configuration.json").write_text('{"foo": 5}')
        monkeypatch.setattr(randovania, "CONFIGURATION_FILE_PATH", tmp_path.joinpath("configuration.json"))
    else:
        tmp_path.joinpath("provided.json").write_text('{"foo": 5}')

    # Run
    config = randovania.get_configuration()

    # Assert
    assert config == {
        "foo": 5,
    }


def test_get_invalid_configuration_file(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    # Setup
    monkeypatch.setattr(randovania, "CONFIGURATION_FILE_PATH", tmp_path.joinpath("configuration.json"))

    # Run
    with pytest.raises(FileNotFoundError):
        randovania.get_configuration()
