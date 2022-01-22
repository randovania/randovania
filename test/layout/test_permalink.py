from unittest.mock import MagicMock, ANY

import pytest

from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink, UnsupportedPermalink


@pytest.fixture(name="fake_generator_parameters")
def _fake_generator_parameters() -> GeneratorParameters:
    parameters = MagicMock(spec=GeneratorParameters)
    parameters.as_bytes = b"\xA0\xB0\xC0"
    return parameters


def test_encode(fake_generator_parameters):
    # Setup
    link = Permalink(
        parameters=fake_generator_parameters,
        seed_hash=None,
        randovania_version=b"0123"
    )

    # Run
    encoded = link.as_base64_str

    # Assert
    assert encoded == "DX4wMTIzAx6sOvRw"


def test_decode(mocker):
    mock_from_bytes: MagicMock = mocker.patch("randovania.layout.generator_parameters.GeneratorParameters.from_bytes",
                                              autospec=True)

    # This test should break whenever we change how permalinks are created
    # When this happens, we must bump the permalink version and change the tests
    encoded = "DX4wMTIzAx6sOvRw"

    expected = Permalink(
        parameters=mock_from_bytes.return_value,
        seed_hash=None,
        randovania_version=b"0123",
    )

    # Uncomment this line to quickly get the new encoded permalink
    # assert expected.as_base64_str == ""
    # print(expected.as_base64_str)

    # Run
    link = Permalink.from_str(encoded)

    # Assert
    assert link == expected
    mock_from_bytes.assert_called_once_with(b"\xA0\xB0\xC0")


@pytest.mark.parametrize("invalid", [
    "",
    "a",
    "x",
    "zz",
    "AAAAfRxALWmCI50gIQD",
    "AAAAfRxALxmCI50gIQDy"
])
def test_decode_invalid(invalid: str):
    with pytest.raises(ValueError):
        Permalink.from_str(invalid)


@pytest.mark.parametrize("seed_hash", [
    None,
    b"12345",
    b"67890",
])
def test_round_trip(seed_hash, fake_generator_parameters, mocker):
    mock_from_bytes: MagicMock = mocker.patch("randovania.layout.generator_parameters.GeneratorParameters.from_bytes",
                                              autospec=True, return_value=fake_generator_parameters)
    # Setup
    link = Permalink(
        parameters=fake_generator_parameters,
        seed_hash=seed_hash,
        randovania_version=b"0123"
    )

    # Run
    after = Permalink.from_str(link.as_base64_str)

    # Assert
    assert link == after
    mock_from_bytes.assert_called_once_with(b"\xA0\xB0\xC0")


@pytest.mark.parametrize(["permalink", "version"], [
    ("CrhkAGTOLJD7Kf6Y", 10),
    ("DLhkAGTOLJD7Kf6Y", 12),
])
def test_decode_old_version(permalink: str, version: int):
    with pytest.raises(ValueError) as exp:
        Permalink.from_str(permalink)

    assert str(exp.value) == (
        "Given permalink has version {}, but this Randovania support only permalink of version {}.".format(
            version, Permalink.current_schema_version()))
